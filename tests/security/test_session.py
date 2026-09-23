from datetime import timedelta

import pytest
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.sessions.models import Session
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from testutils.factories import RegistrationFactory, UserFactory

from aurora.tasks import clear_expired_sessions


@pytest.fixture
def user(db):
    return UserFactory()


def _session_cookie(client: Client) -> str:
    return client.cookies[settings.SESSION_COOKIE_NAME].value


def test_session_cookie_is_hidden_from_scripts(db, rf):
    middleware = SessionMiddleware(lambda request: HttpResponse())
    request = rf.get("/")
    middleware.process_request(request)
    request.session["touched"] = True

    cookie = middleware.process_response(request, HttpResponse()).cookies[settings.SESSION_COOKIE_NAME]

    assert cookie["httponly"]
    assert cookie["samesite"] == "Lax"


def test_sessions_are_stored_server_side():
    assert settings.SESSION_ENGINE == "django.contrib.sessions.backends.cached_db"


def test_a_copied_session_cookie_is_useless_after_logout(user, client):
    client.force_login(user)
    copied = _session_cookie(client)
    assert client.get("/api/user/me/").json()["authenticated"]

    client.post(reverse("logout"))

    replay = Client()
    replay.cookies[settings.SESSION_COOKIE_NAME] = copied
    assert replay.get("/api/user/me/").json()["authenticated"] is False


def test_version_endpoint_does_not_publish_the_session_cookie(user, client):
    registration = RegistrationFactory()
    client.force_login(user)
    cookie = _session_cookie(client)

    response = client.get(f"/api/registration/{registration.pk}/version/")

    assert response.json()["session_id"]
    assert cookie not in response.content.decode()


def test_registration_page_does_not_publish_the_session_cookie(user, client, simple_form):
    registration = RegistrationFactory(flex_form=simple_form)
    client.force_login(user)
    cookie = _session_cookie(client)

    response = client.get(reverse("register", args=[registration.slug, registration.version]), follow=True)

    assert response.status_code == 200
    assert cookie not in response.content.decode()


def test_expired_sessions_are_purged(db):
    Session.objects.create(session_key="expired", session_data="", expire_date=timezone.now() - timedelta(days=1))
    Session.objects.create(session_key="current", session_data="", expire_date=timezone.now() + timedelta(days=1))

    clear_expired_sessions()

    assert list(Session.objects.values_list("session_key", flat=True)) == ["current"]
