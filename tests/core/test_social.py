from unittest import mock
from unittest.mock import MagicMock

import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from social_core.exceptions import InvalidEmail

from aurora.core.authentication import create_user, redir_to_form, require_email, social_details, user_details
from aurora.security.models import User


@override_settings(SOCIAL_AUTH_GOOGLE_OAUTH2_KEY="1", SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET="2")
def test_social_login(db, client):
    """Test login with SSO."""
    session = client.session
    session["google-oauth2_state"] = "1"
    session.save()

    res = client.get(reverse("social:begin", kwargs={"backend": "azuread-tenant-oauth2"}))
    assert res.status_code == 302

    with (
        mock.patch("social_core.backends.base.BaseAuth.request") as mock_request,
        mock.patch(
            "social_core.backends.azuread_tenant.AzureADTenantOAuth2.user_data",
            return_value={"email": "user@wxample.com"},
        ),
        mock.patch("social_core.backends.oauth.OAuthAuth.validate_state", return_value={}),
    ):
        url = reverse("social:complete", kwargs={"backend": "azuread-tenant-oauth2"})
        url += "?code=2&state=1"
        mock_request.return_value.json.return_value = {"access_token": "123"}
        with mock.patch(
            "django.contrib.sessions.backends.base.SessionBase.set_expiry",
            side_effect=[OverflowError, None],
        ):
            response = client.get(url)
    assert response.status_code == 302
    assert response.url == settings.LOGIN_REDIRECT_URL
    assert User.objects.filter(email="user@wxample.com").exists()


@pytest.mark.parametrize("details", [{}, {"email": "user@wxample.com"}], ids=["Emoty", "email"])
@pytest.mark.parametrize(
    "user_data", [{}, {"email": "user2@wxample.com"}, {"signInNames.emailAddress": "user2@wxample.com"}]
)
def test_social_details(user_data, details):
    expected = details.get("email", None) or (list(user_data.values())[0] if user_data else None)
    res = social_details(
        backend=MagicMock(user_data=MagicMock(return_value=user_data)), details=details, response={"idp": "IDP"}
    )
    assert res == {"details": {"email": expected, "idp": "IDP"}}


def test_social_user_details(user):
    with mock.patch("aurora.core.authentication.social_core_user.user_details", return_value=user):
        assert (
            user_details(
                strategy=MagicMock(user_details=lambda *args: None),
                details={"email": "user@wxample.com"},
                backend=MagicMock(),
                user=user,
            )
            == user
        )


def test_social_user_details_keeps_existing_names(user):
    user.first_name = "Existing"
    user.last_name = "Name"
    with mock.patch("aurora.core.authentication.social_core_user.user_details", return_value=user):
        result = user_details(
            strategy=MagicMock(user_details=lambda *args: None),
            details={"email": "user@wxample.com", "first_name": "", "last_name": ""},
            backend=MagicMock(),
            user=user,
        )

    user.refresh_from_db()
    assert result == user
    assert user.first_name == "Existing"
    assert user.last_name == "Name"
    assert user.username == "user@wxample.com"


def test_require_email():
    with pytest.raises(InvalidEmail):
        assert require_email(MagicMock(), details={}, is_new=True)
    require_email(MagicMock(), details={"email": "user@wxample.com"})


def test_require_email_returns_for_existing_user_with_email(db):
    existing_user = User.objects.create(email="existing@wxample.com", username="existing@wxample.com")
    assert require_email(MagicMock(), details={}, user=existing_user, is_new=True) is None


def test_create_user(db):
    assert create_user(None, {"email": "user@wxample.com", "first_name": "first_name", "last_name": "last_name"})
    assert User.objects.filter(email="user@wxample.com").exists()


def test_create_user_returns_existing_user_as_not_new(db):
    existing_user = User.objects.create(email="existing@wxample.com", username="existing@wxample.com")
    assert create_user(None, {"email": "new@wxample.com"}, user=existing_user) == {"is_new": False}


def test_redir_to_form_creates_user(db):
    result = redir_to_form(None, {"email": "user-redir@wxample.com", "first_name": "first", "last_name": "last"})
    assert result["is_new"] is True
    assert result["user"].email == "user-redir@wxample.com"
    assert User.objects.filter(email="user-redir@wxample.com").exists()


def test_redir_to_form_returns_existing_user_as_not_new(db):
    existing_user = User.objects.create(email="existing-redir@wxample.com", username="existing-redir@wxample.com")
    assert redir_to_form(None, {"email": "new@wxample.com"}, user=existing_user) == {"is_new": False}
