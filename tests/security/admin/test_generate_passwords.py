import pytest
from unittest.mock import Mock, patch
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from aurora.security.admin import UserAdmin, generate_passwords
from testutils.factories import UserFactory, SuperUserFactory


User = get_user_model()


@pytest.fixture
def admin_user():
    return SuperUserFactory(username="admin", email="admin@test.com")


@pytest.fixture
def user_queryset(db):
    users = [
        UserFactory(username="user1", email="user1@test.com", first_name="User", last_name="One"),
        UserFactory(username="user2", email="user2@test.com", first_name="User", last_name="Two"),
        UserFactory(username="user3", email="user3@test.com", first_name="User", last_name="Three"),
    ]
    return User.objects.filter(pk__in=[u.pk for u in users])


@pytest.fixture
def mock_request(admin_user):
    factory = RequestFactory()
    request = factory.post("/admin/")
    request.user = admin_user
    request._messages = Mock()
    return request


@pytest.fixture
def user_admin():
    return UserAdmin(User, Mock())


@pytest.mark.django_db
@patch("aurora.security.admin.generate_pwd")
def test_generate_passwords_success(mock_generate_pwd, mock_request, user_admin, user_queryset):
    mock_generate_pwd.return_value = "Password sent to User!"
    mock_request.user.has_perm = Mock(return_value=True)

    generate_passwords(user_admin, mock_request, user_queryset)

    assert mock_generate_pwd.call_count == user_queryset.count()


@pytest.mark.django_db
@patch("aurora.security.admin.generate_pwd")
@patch("aurora.security.admin.messages")
def test_generate_passwords_permission_denied(
    mock_messages, mock_generate_pwd, mock_request, user_admin, user_queryset
):
    mock_request.user.has_perm = Mock(return_value=False)

    generate_passwords(user_admin, mock_request, user_queryset)

    mock_request.user.has_perm.assert_called_once_with("security.add_aurorauser")
    mock_messages.error.assert_called_once_with(mock_request, "Sorry you do not have rights to execute this action")
    mock_generate_pwd.assert_not_called()


@pytest.mark.django_db
@patch("aurora.security.admin.generate_pwd")
@patch("aurora.security.admin.messages")
def test_generate_passwords_success_message(mock_messages, mock_generate_pwd, mock_request, user_admin, user_queryset):
    mock_generate_pwd.return_value = "Password sent!"
    mock_request.user.has_perm = Mock(return_value=True)

    generate_passwords(user_admin, mock_request, user_queryset)

    expected_count = user_queryset.count()
    mock_messages.success.assert_called_once_with(mock_request, f"{expected_count} have been sent!")


def test_user_admin_has_generate_passwords_action():
    user_admin = UserAdmin(User, Mock())
    assert generate_passwords in user_admin.actions
