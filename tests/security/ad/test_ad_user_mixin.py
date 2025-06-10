import pytest
from unittest.mock import patch
from django.http import Http404
from django.contrib import messages
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from aurora.security.admin import UserAdmin
from aurora.security.models import User


@pytest.fixture
def admin_site():
    return AdminSite()


@pytest.fixture
def ad_user_admin_instance(admin_site):
    return UserAdmin(User, admin_site)


@pytest.fixture
def user_with_profile(user):
    user.profile.ad_uuid = "21d2ecba-83e4-4e81-a93c-d44f55dd222e"
    user.profile.save()
    return user


@pytest.fixture
def user_without_profile(user):
    return user


@pytest.fixture
def mock_user_data():
    return {
        "mail": "test@unicef.org",
        "givenName": "Test",
        "surname": "User",
        "id": "21d2ecba-83e4-4e81-a93c-d44f55dd222e",
    }


@pytest.fixture
def user_with_sync_permissions(user) -> User:
    content_type, created = ContentType.objects.get_or_create(app_label="account", model="user")
    permission, created = Permission.objects.get_or_create(
        codename="can_sync_with_ad", content_type=content_type, defaults={"name": "Can sync with AD"}
    )
    user.user_permissions.add(permission)
    return user


def test_sync_ad_data_with_profile_uuid_success(ad_user_admin_instance, user_with_profile, mock_user_data):
    with patch("aurora.security.ad.MicrosoftGraphAPI") as mock_graph:
        mock_graph.return_value.get_user_data.return_value = mock_user_data

        ad_user_admin_instance._sync_ad_data(user_with_profile)

        user_with_profile.refresh_from_db()
        assert user_with_profile.username == "test@unicef.org"
        assert user_with_profile.email == "test@unicef.org"
        assert user_with_profile.first_name == "Test"
        assert user_with_profile.last_name == "User"

        mock_graph.return_value.get_user_data.assert_called_with(uuid="21d2ecba-83e4-4e81-a93c-d44f55dd222e")


def test_sync_ad_data_without_profile_uuid_success(ad_user_admin_instance, user_without_profile, mock_user_data):
    with patch("aurora.security.ad.MicrosoftGraphAPI") as mock_graph:
        mock_user_data_updated = mock_user_data.copy()
        mock_user_data_updated["mail"] = user_without_profile.email
        mock_graph.return_value.get_user_data.return_value = mock_user_data_updated

        ad_user_admin_instance._sync_ad_data(user_without_profile)

        user_without_profile.refresh_from_db()
        assert user_without_profile.username == user_without_profile.email
        assert user_without_profile.first_name == "Test"
        assert user_without_profile.last_name == "User"

        mock_graph.return_value.get_user_data.assert_called_with(email=user_without_profile.email)


def test_sync_ad_data_all_lookups_fail(ad_user_admin_instance, user_with_profile):
    with patch("aurora.security.ad.MicrosoftGraphAPI") as mock_graph:
        mock_graph.return_value.get_user_data.side_effect = Http404()

        with pytest.raises(Http404):
            ad_user_admin_instance._sync_ad_data(user_with_profile)

        assert mock_graph.return_value.get_user_data.call_count == 2


def test_sync_ad_data_no_profile_lookup_fails(ad_user_admin_instance, user_without_profile):
    with patch("aurora.security.ad.MicrosoftGraphAPI") as mock_graph:
        mock_graph.return_value.get_user_data.side_effect = Http404()

        with pytest.raises(Http404):
            ad_user_admin_instance._sync_ad_data(user_without_profile)

        mock_graph.return_value.get_user_data.assert_called_once_with(email=user_without_profile.email)


@pytest.mark.django_db
def test_sync_multi_all_users_success(user_with_sync_permissions, ad_user_admin_instance, client):
    client.force_login(user_with_sync_permissions)

    with patch("aurora.security.ad.ADUSerMixin._sync_ad_data") as mock_sync:
        url = reverse("admin:security_user_sync_multi")
        response = client.post(url)

        assert mock_sync.call_count == 1
        mock_sync.assert_any_call(user_with_sync_permissions)
        user_messages = list(response.wsgi_request._messages)
        assert len(user_messages) == 1
        assert user_messages[0].message == "Active Directory data successfully fetched"
        assert user_messages[0].level == messages.SUCCESS


@pytest.mark.django_db
def test_sync_multi_users_not_found(user_with_sync_permissions, ad_user_admin_instance, client):
    client.force_login(user_with_sync_permissions)

    with patch("aurora.security.ad.ADUSerMixin._sync_ad_data", side_effect=Http404()):
        url = reverse("admin:security_user_sync_multi")
        response = client.post(url)
        assert response.status_code == 302
        user_messages = list(response.wsgi_request._messages)
        assert len(user_messages) == 1
        assert user_messages[0].message == f"These users were not found: {user_with_sync_permissions.username}"
        assert user_messages[0].level == messages.WARNING


@pytest.mark.django_db
def test_sync_multi_exception_handling(user_with_sync_permissions, ad_user_admin_instance, client):
    test_exception = Exception("Unexpected error")

    client.force_login(user_with_sync_permissions)

    with patch("aurora.security.ad.ADUSerMixin._sync_ad_data", side_effect=test_exception):
        url = reverse("admin:security_user_sync_multi")
        response = client.post(url)
        assert response.status_code == 302

        user_messages = list(response.wsgi_request._messages)
        assert user_messages[0].message == "Unexpected error"
        assert user_messages[0].level == messages.ERROR


@pytest.mark.django_db
def test_sync_multi_empty_queryset(user_with_sync_permissions, ad_user_admin_instance, client):
    client.force_login(user_with_sync_permissions)

    with patch("aurora.security.ad.ADUSerMixin._sync_ad_data") as mock_sync:
        with patch("aurora.security.admin.UserAdmin.get_queryset", return_value=[]):
            url = reverse("admin:security_user_sync_multi")
            response = client.post(url)

            mock_sync.assert_not_called()
            assert response.status_code == 302
            user_messages = list(response.wsgi_request._messages)
            assert len(user_messages) == 1
            assert user_messages[0].message == "Active Directory data successfully fetched"
            assert user_messages[0].level == messages.SUCCESS
