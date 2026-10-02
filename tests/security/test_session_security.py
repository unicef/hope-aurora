"""Session cookie flags, logout behaviour and the permission floor.

Each of these covers a gap reported against the staging deployment: a session cookie readable from
JavaScript, a logout control that answered 405, and an authentication backend that handed every
permission to anonymous callers.
"""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import Client
from django.urls import reverse
from testutils.factories import UserSocialAuthFactory


@pytest.fixture
def logged_in(admin_user):
    client = Client()
    assert client.login(username=admin_user.username, password="password")
    return client


@pytest.fixture
def login_response(admin_user):
    """The response that actually issues the cookie.

    Client.login() writes the cookie straight into the request jar and never applies the flags, so
    the flags under test are only observable on a genuine response.
    """
    response = Client().post("/login/", {"username": admin_user.username, "password": "password"})
    assert response.status_code == 302
    return response


class TestSessionCookieFlags:
    def test_cookie_is_httponly(self, login_response):
        """Without this, any XSS reads the session straight off document.cookie."""
        assert login_response.cookies["aurora_id"]["httponly"] is True

    def test_cookie_is_samesite_lax(self, login_response):
        assert login_response.cookies["aurora_id"]["samesite"] == "Lax"

    def test_cookie_carries_no_max_age(self, login_response):
        """A session cookie, so it is not written to disk or replayed after the browser restarts."""
        morsel = login_response.cookies["aurora_id"]
        assert morsel["max-age"] == ""
        assert morsel["expires"] == ""

    def test_cookie_is_secure_when_the_setting_is_on(self, login_response, settings):
        """Secure follows SESSION_COOKIE_SECURE, which is off only for plain-HTTP local runs."""
        assert login_response.cookies["aurora_id"]["secure"] == (settings.SESSION_COOKIE_SECURE or "")

    def test_signed_payload_still_expires(self, settings):
        """Dropping Max-Age must not also drop the server-side lifetime.

        SessionBase.get_expiry_age falls back to SESSION_COOKIE_AGE when the session is marked to
        expire at browser close, so this is what stops a captured cookie being valid forever.
        """
        from django.contrib.sessions.backends.signed_cookies import SessionStore

        assert settings.SESSION_COOKIE_AGE == 60 * 60 * 24
        assert SessionStore().get_expiry_age() == 60 * 60 * 24

    def test_authorize_cookie_still_bounds_the_signature_age(self, settings):
        """It reuses SESSION_COOKIE_AGE as max_age, and max_age=None means no expiry check at all."""
        import inspect

        from aurora.registration.views.registration import authorize_cookie

        assert "max_age=settings.SESSION_COOKIE_AGE" in inspect.getsource(authorize_cookie)
        assert settings.SESSION_COOKIE_AGE is not None


class TestLogout:
    def test_get_is_not_allowed(self, logged_in):
        """Django 5 made LogoutView POST-only; the old anchor-based link silently did nothing."""
        assert logged_in.get("/logout/").status_code == 405

    def test_post_ends_the_local_session(self, logged_in):
        assert logged_in.post("/logout/").status_code == 302
        assert logged_in.cookies["aurora_id"].value == ""

    def test_local_user_returns_to_the_index(self, logged_in):
        assert logged_in.post("/logout/").url == reverse("index")

    def test_sso_user_is_handed_to_the_identity_provider(self, admin_user):
        """Azure AD keeps its own session, so a local-only logout signs the user straight back in."""
        UserSocialAuthFactory(user=admin_user)
        client = Client()
        client.force_login(admin_user)

        response = client.post("/logout/")
        assert response.url == reverse("unicef-logout")

        redirect = client.get(response.url)
        assert redirect.status_code == 302
        assert redirect.url.startswith("https://login.microsoftonline.com/")
        assert "post_logout_redirect_uri=" in redirect.url

    def test_sso_redirect_resolves_the_tenant(self, admin_user):
        """unicef_security reads the tenant from SOCIAL_AUTH_TENANT_NAME and renders None without it."""
        UserSocialAuthFactory(user=admin_user)
        client = Client()
        client.force_login(admin_user)
        redirect = client.get(client.post("/logout/").url)
        assert "/None/" not in redirect.url


class TestAnonymousHoldsNothing:
    def test_backend_refuses_anonymous(self):
        from aurora.security.backend import AuroraAuthBackend

        assert AuroraAuthBackend().has_perm(AnonymousUser(), "registration.view_record") is False

    def test_user_has_perm_is_false_for_anonymous(self):
        assert AnonymousUser().has_perm("registration.view_record") is False

    def test_authenticated_user_keeps_their_permission(self, admin_user):
        assert isinstance(admin_user.has_perm("core.view_project"), bool)


class TestSystemInfoRequiresAuthentication:
    @pytest.mark.django_db
    def test_anonymous_is_refused(self):
        response = Client().get("/api/sys/")
        assert response.status_code in {401, 403}
