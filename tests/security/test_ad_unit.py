from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django.contrib import admin
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.http import Http404

from aurora.security.ad import ADUSerMixin, LoadUsersForm, build_arg_dict_from_dict
from aurora.core.models import Organization
from aurora.security.models import User


class _AdAdmin(ADUSerMixin):
    pass


@pytest.fixture
def ad_admin():
    return _AdAdmin(User, admin.site)


def test_build_arg_dict_from_dict_maps_fields():
    data = {"mail": "user@example.org", "givenName": "Alice"}
    mapping = {"email": "mail", "first_name": "givenName", "last_name": "surname"}
    assert build_arg_dict_from_dict(data, mapping) == {
        "email": "user@example.org",
        "first_name": "Alice",
        "last_name": None,
    }


def test_load_users_form_validates_emails_and_scope():
    form = LoadUsersForm()
    form.cleaned_data = {"emails": "ok@example.org invalid-email"}
    with pytest.raises(ValidationError, match="Invalid emails"):
        form.clean_emails()

    form.cleaned_data = {"organization": None, "project": None, "registration": None}
    with pytest.raises(ValidationError, match="must set one scope"):
        form.clean()

    form.cleaned_data = {"organization": object(), "project": object(), "registration": None}
    with pytest.raises(ValidationError, match="must set only one scope"):
        form.clean()


@pytest.mark.django_db
def test_get_ad_form_respects_request_method(ad_admin, rf):
    req_get = rf.get("/admin/")
    req_post = rf.post("/admin/", data={})
    assert isinstance(ad_admin._get_ad_form(req_get), LoadUsersForm)
    assert isinstance(ad_admin._get_ad_form(req_post), LoadUsersForm)


@pytest.mark.django_db
def test_sync_ad_data_uses_fallback_filter(monkeypatch, ad_admin):
    user = User.objects.create(username="u1", email="u1@example.org")
    user.profile.ad_uuid = "uuid-1"
    user.profile.save()

    calls = []

    class _Graph:
        def get_user_data(self, **kwargs):
            calls.append(kwargs)
            if "uuid" in kwargs:
                raise Http404
            return {"mail": "u1@example.org", "givenName": "A", "surname": "B"}

    monkeypatch.setattr("aurora.security.ad.MicrosoftGraphAPI", lambda: _Graph())
    ad_admin._sync_ad_data(user)
    user.refresh_from_db()
    assert calls[0] == {"uuid": "uuid-1"}
    assert calls[1] == {"email": "u1@example.org"}
    assert user.first_name == "A"
    assert user.last_name == "B"


@pytest.mark.django_db
def test_sync_ad_data_raises_when_not_found(monkeypatch, ad_admin):
    user = User.objects.create(username="u2", email="u2@example.org")

    class _Graph:
        @staticmethod
        def get_user_data(**kwargs):
            raise Http404

    monkeypatch.setattr("aurora.security.ad.MicrosoftGraphAPI", lambda: _Graph())
    with pytest.raises(Http404):
        ad_admin._sync_ad_data(user)


@pytest.mark.django_db
def test_sync_multi_success_and_not_found(monkeypatch, ad_admin, rf):
    req = rf.get("/admin/")
    u1 = User.objects.create(username="u1", email="u1@example.org")
    u2 = User.objects.create(username="u2", email="u2@example.org")
    ad_admin.get_queryset = lambda _r: [u1, u2]
    ad_admin.message_user = Mock()

    def _sync(user):
        if user == u2:
            raise Http404

    monkeypatch.setattr(ad_admin, "_sync_ad_data", _sync)
    ad_admin.sync_multi.func(ad_admin, req)
    ad_admin.message_user.assert_called_once()


@pytest.mark.django_db
def test_sync_multi_all_success(monkeypatch, ad_admin, rf):
    req = rf.get("/admin/")
    u1 = User.objects.create(username="u1ok", email="u1ok@example.org")
    ad_admin.get_queryset = lambda _r: [u1]
    ad_admin.message_user = Mock()
    monkeypatch.setattr(ad_admin, "_sync_ad_data", lambda *_a, **_k: None)
    ad_admin.sync_multi.func(ad_admin, req)
    ad_admin.message_user.assert_called_once()


@pytest.mark.django_db
def test_sync_multi_outer_exception(monkeypatch, ad_admin, rf):
    req = rf.get("/admin/")
    ad_admin.get_queryset = lambda _r: (_ for _ in ()).throw(RuntimeError("boom"))
    ad_admin.message_user = Mock()
    ad_admin.sync_multi.func(ad_admin, req)
    ad_admin.message_user.assert_called_once()


@pytest.mark.django_db
def test_sync_single_handles_exception(monkeypatch, ad_admin, rf):
    req = rf.get("/admin/")
    ad_admin.get_object = lambda *_a, **_k: User.objects.create(username="u3", email="u3@example.org")
    ad_admin.message_user = Mock()
    monkeypatch.setattr(ad_admin, "_sync_ad_data", lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("boom")))
    ad_admin.sync_single.func(ad_admin, req, "1")
    ad_admin.message_user.assert_called_once()


@pytest.mark.django_db
def test_load_ad_users_invalid_form_returns_context(monkeypatch, ad_admin, rf):
    req = rf.post("/admin/", data={})
    req.user = SimpleNamespace(pk=1)
    req.session = SimpleNamespace(session_key="abc")
    ad_admin.get_common_context = lambda *_a, **_k: {}

    invalid_form = Mock()
    invalid_form.is_valid.return_value = False
    monkeypatch.setattr(ad_admin, "_get_ad_form", lambda *_a, **_k: invalid_form)
    response = ad_admin.load_ad_users.func(ad_admin, req)
    assert response.status_code == 200


@pytest.mark.django_db
def test_load_ad_users_graph_disabled_creates_entries(monkeypatch, ad_admin, rf):
    request = rf.post("/admin/", data={})
    request.user = SimpleNamespace(pk=1)
    request.session = SimpleNamespace(session_key="abc")
    ad_admin.get_common_context = lambda *_a, **_k: {}
    role = Group.objects.create(name="role-1")
    org = Organization.objects.create(name="Org Scope", slug="org-scope")

    form = Mock()
    form.is_valid.return_value = True
    form.cleaned_data = {
        "emails": "new1@example.org new2@example.org",
        "role": role,
        "organization": org,
        "project": None,
        "registration": None,
    }
    monkeypatch.setattr(ad_admin, "_get_ad_form", lambda *_a, **_k: form)
    monkeypatch.setattr("aurora.security.ad.config", SimpleNamespace(GRAPH_API_ENABLED=False))
    monkeypatch.setattr("aurora.security.ad.User.objects.bulk_create", lambda objs: objs)
    monkeypatch.setattr("aurora.security.ad.AuroraRole.objects.bulk_create", lambda objs, ignore_conflicts=True: objs)

    response = ad_admin.load_ad_users.func(ad_admin, request)
    assert response.status_code == 200
