import json
from hashlib import md5
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from django.core import signing
from django.core.exceptions import ValidationError
from django.http import Http404
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import reverse
from django.utils.translation import override
from testutils.factories import RegistrationFactory
from testutils.factories import RecordFactory

from aurora.registration.views.registration import BinaryFile
from aurora.registration.views.registration import RegisterCompleteView
from aurora.registration.views.registration import RegisterRouter
from aurora.registration.views.registration import RegisterView
from aurora.security.models import User


@pytest.mark.django_db
def test_registrations_get_lists_only_active(client):
    active_reg = RegistrationFactory(active=True)
    RegistrationFactory(active=False)

    response = client.get(reverse("registrations"))

    assert response.status_code == 200
    registrations = list(response.context["registrations"])
    assert registrations == [active_reg]


@pytest.mark.django_db
def test_registrations_post_sets_single_pwa_enabled(client):
    enabled = RegistrationFactory(active=True, is_pwa_enabled=True)
    target = RegistrationFactory(active=True, is_pwa_enabled=False)

    response = client.post(reverse("registrations"), data={"slug": target.slug})

    enabled.refresh_from_db()
    target.refresh_from_db()
    assert response.status_code == 200
    assert target.is_pwa_enabled is True
    assert enabled.is_pwa_enabled is False


@pytest.mark.django_db
def test_get_pwa_enabled_returns_nulls_when_missing(client):
    response = client.get(reverse("get_pwa_enabled"))
    assert response.status_code == 200
    assert response.json() == {"slug": None, "version": None, "publicKey": None, "optionsSets": None}


@pytest.mark.django_db
def test_get_pwa_enabled_returns_selected_registration(client):
    reg = RegistrationFactory(is_pwa_enabled=True)

    response = client.get(reverse("get_pwa_enabled"))
    data = response.json()

    assert response.status_code == 200
    assert data["slug"] == reg.slug
    assert data["version"] == reg.version


@pytest.mark.django_db
def test_authorize_cookie_returns_true_for_valid_user(client):
    user = User.objects.create_user(username="cookie-user", email="cookie@example.com", password="password")
    signed_data = signing.dumps(
        {"_auth_user_id": str(user.id)},
        salt="django.contrib.sessions.backends.signed_cookies",
    )

    response = client.post(reverse("authorize_cookie"), data=json.dumps(signed_data), content_type="application/json")

    assert response.status_code == 200
    assert response.json() == {"authorized": True}


@pytest.mark.django_db
def test_authorize_cookie_returns_false_for_invalid_payload(client):
    response = client.post(
        reverse("authorize_cookie"),
        data=json.dumps("invalid-value"),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json() == {"authorized": False}


@pytest.mark.django_db
def test_authorize_cookie_returns_false_when_user_not_found(client):
    signed_data = signing.dumps(
        {"_auth_user_id": "999999"},
        salt="django.contrib.sessions.backends.signed_cookies",
    )

    response = client.post(reverse("authorize_cookie"), data=json.dumps(signed_data), content_type="application/json")

    assert response.status_code == 200
    assert response.json() == {"authorized": False}


@pytest.mark.django_db
def test_registration_router_redirects_to_registration_url(client, monkeypatch):
    mocked_reg = Mock()
    mocked_reg.locale = "en-us"
    mocked_reg.all_locales = ["en-us"]
    mocked_reg.get_absolute_url.return_value = "/en-us/register/fake/"
    mocked_qs = Mock()
    mocked_qs.get.return_value = mocked_reg
    monkeypatch.setattr("aurora.registration.views.registration.Registration.objects.only", lambda *a: mocked_qs)

    with override("it-it"):
        response = client.post(reverse("registration-router"), data={"slug": "fake"})

    assert response.status_code == 302
    assert "fake" in response.headers["Location"]
    assert "/register/" in response.headers["Location"]


@pytest.mark.django_db
def test_register_verify_uses_hash_validation(client):
    record = RecordFactory()
    record.storage = b"qr-payload"
    record.save(update_fields=["storage"])
    valid_hash = md5(record.storage).hexdigest()

    ok_response = client.get(reverse("register-verify", args=[record.pk, valid_hash]))
    ko_response = client.get(reverse("register-verify", args=[record.pk, "wrong-hash"]))

    assert ok_response.status_code == 200
    assert ok_response.context["valid"] is True
    assert ko_response.status_code == 200
    assert ko_response.context["valid"] is False


@pytest.mark.django_db
def test_register_done_returns_404_for_missing_record(client):
    reg = RegistrationFactory()
    response = client.get(reverse("register-done", args=[reg.pk, 999999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_register_done_404_collect_messages_triggers_lookup(client):
    from aurora.state import state

    reg = RegistrationFactory()
    view = RegisterCompleteView()
    view.kwargs = {"reg": reg.pk, "rec": 999999}
    state.collect_messages = True
    try:
        with patch("aurora.registration.views.registration.Record.objects.first") as first_lookup:
            with pytest.raises(Http404):
                _ = view.record
            first_lookup.assert_called_once()
    finally:
        state.collect_messages = False


@pytest.mark.django_db
def test_register_auth_returns_project_and_user_details(client):
    reg = RegistrationFactory()
    response = client.get(reverse("register-auth", args=[reg.slug]))
    data = response.json()

    assert response.status_code == 200
    assert data["registration"]["name"] == reg.name
    assert data["registration"]["protected"] == reg.protected
    assert data["user"]["anonymous"] is True


def test_binary_file_exposes_content():
    payload = b"payload"
    wrapped = BinaryFile(payload)
    assert wrapped.content == payload


def test_register_router_helper_methods_return_defaults():
    view = RegisterRouter()
    assert view.get_template_names() == []
    assert view.get_form() is None


@pytest.mark.django_db
def test_register_router_uses_current_language_when_supported(client, monkeypatch):
    mocked_reg = Mock()
    mocked_reg.locale = "en-us"
    mocked_reg.all_locales = ["it-it", "en-us"]
    mocked_reg.get_absolute_url.return_value = "/it-it/register/fake/"
    mocked_qs = Mock()
    mocked_qs.get.return_value = mocked_reg
    monkeypatch.setattr("aurora.registration.views.registration.Registration.objects.only", lambda *a: mocked_qs)

    with override("it-it"):
        response = client.post(reverse("registration-router"), data={"slug": "fake"})

    assert response.status_code == 302
    assert response.headers["Location"] == "/it-it/register/fake/"


@pytest.mark.django_db
def test_registrations_returns_none_for_non_get_post():
    from aurora.registration.views.registration import registrations

    request = RequestFactory().put(reverse("registrations"))
    assert registrations(request) is None


@pytest.mark.django_db
def test_register_auth_returns_404_for_missing_registration(client):
    response = client.get(reverse("register-auth", args=["missing-slug"]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_register_redirects_when_language_not_supported(client):
    reg = RegistrationFactory(locale="en-us", locales=["en-us"])
    with override("fr-fr"):
        response = client.get(reverse("register", args=[reg.slug]))
    assert response.status_code == 302


def test_register_view_validate_appends_validator_error():
    view = RegisterView()
    view.errors = []
    view.registration = Mock(
        validator=Mock(validate=Mock(side_effect=ValidationError("invalid"))),
        get_unique_value=Mock(return_value=None),
        unique_field_error="must be unique",
    )

    assert view.validate({"first_name": "x"}) is False
    assert len(view.errors) == 1


def test_register_complete_context_without_qrcode(monkeypatch):
    from aurora.registration.views import registration as registration_views

    reg = Mock(get_absolute_url=Mock(return_value="/register/foo/"))
    record = Mock(registration=reg)
    view = RegisterCompleteView()
    view.record = record
    view.registration = reg

    monkeypatch.setattr(registration_views, "config", Mock(QRCODE=False))
    context = view.get_context_data()
    assert context["qrcode"] is None
    assert context["url"] is None


def test_register_view_get_uses_collect_messages_cache_path(monkeypatch):
    from aurora.registration.views import registration as registration_views
    from aurora.state import state

    view = RegisterView()
    request = RequestFactory().get("/register/fake/")
    request.user = Mock(is_anonymous=True, is_staff=False)
    view.registration = Mock(protected=False)

    monkeypatch.setattr(state, "collect_messages", True)
    monkeypatch.setattr(registration_views, "get_etag", lambda *args: "etag-value")
    cached = HttpResponse(status=304)
    monkeypatch.setattr(registration_views, "get_conditional_response", lambda *args: cached)

    response = view.get(request)
    assert response.status_code == 304


def test_register_view_form_valid_returns_http_response_directly(monkeypatch):
    from aurora.state import state

    view = RegisterView()
    view.registration = Mock(add_record=Mock(return_value=HttpResponse("ok")))
    form = Mock(cleaned_data={}, indexes={"1": None, "2": None, "3": None})
    form.get_counters.return_value = {}

    monkeypatch.setattr(state, "collect_messages", False)
    response = view.form_valid(form, {})
    assert isinstance(response, HttpResponse)
    assert response.content == b"ok"


def test_register_view_form_valid_sets_index2_and_index3(monkeypatch):
    from aurora.state import state

    record = Mock(pk=123)
    view = RegisterView()
    view.registration = Mock(add_record=Mock(return_value=record), pk=77)
    form = Mock(
        cleaned_data={"a": 1, "path2": "v2", "path3": "v3"},
        indexes={"1": None, "2": "path2", "3": "path3"},
    )
    form.get_counters.return_value = {}

    monkeypatch.setattr(state, "collect_messages", False)
    response = view.form_valid(form, {})

    submitted_data = view.registration.add_record.call_args.args[0]
    assert submitted_data["index2"] == "v2"
    assert submitted_data["index3"] == "v3"
    assert response.status_code == 302


def test_register_view_form_invalid_logs_when_enabled(monkeypatch):
    from aurora.registration.views import registration as registration_views

    view = RegisterView()
    view.errors = [ValidationError("bad")]
    view.target = "target-field"
    view.get_context_data = Mock(return_value={})
    view.render_to_response = Mock(return_value=HttpResponse("invalid"))
    form = Mock(errors={"field": ["bad"]})
    formsets = {"fs": Mock(errors={"x": ["err"]})}

    class _Scope:
        def set_extra(self, *args, **kwargs):
            return None

    class _ScopeCtx:
        def __enter__(self):
            return _Scope()

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(registration_views, "config", Mock(LOG_POST_ERRORS=True))
    monkeypatch.setattr(registration_views.sentry_sdk, "push_scope", lambda: _ScopeCtx())
    logger_error = Mock()
    monkeypatch.setattr(registration_views.logger, "error", logger_error)

    response = view.form_invalid(form, formsets)
    assert response.content == b"invalid"
    logger_error.assert_called_once()
