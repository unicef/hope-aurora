import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django.contrib import admin
from django.http import HttpResponse

from aurora.registration.admin.record import RecordAdmin
from aurora.registration.models import Record


@pytest.fixture
def record_admin():
    return RecordAdmin(Record, admin.site)


def test_get_queryset_applies_defer_and_select_related(record_admin, monkeypatch, rf):
    qs = Mock()
    qs.defer.return_value = qs
    qs.select_related.return_value = "final"
    monkeypatch.setattr(
        "smart_admin.modeladmin.SmartModelAdmin.get_queryset",
        lambda *_a, **_k: qs,
    )
    request = rf.get("/admin/")
    assert record_admin.get_queryset(request) == "final"
    qs.defer.assert_called_once_with("fields", "files")
    qs.select_related.assert_called_once_with("registration", "registrar")


def test_get_common_context_and_changeform_view(record_admin, monkeypatch, rf):
    request = rf.get("/admin/")
    monkeypatch.setattr(
        "smart_admin.modeladmin.SmartModelAdmin.get_common_context",
        lambda *_a, **kwargs: kwargs,
    )
    monkeypatch.setattr(
        "aurora.registration.admin.record.is_root",
        lambda *_a, **_k: True,
    )
    ctx = record_admin.get_common_context(request, "1", title="T")
    assert ctx["is_root"] is True
    assert ctx["title"] == "T"

    called = {}

    def _changeform(_self, _request, _obj_id, _form_url, extra_context):
        called["extra"] = extra_context
        return HttpResponse("ok")

    monkeypatch.setattr(
        "smart_admin.modeladmin.SmartModelAdmin.changeform_view",
        _changeform,
    )
    response = record_admin.changeform_view(request, "1")
    assert response.status_code == 200
    assert called["extra"] == {"is_root": True}


def test_receipt_sets_href_and_logs_exception(record_admin, monkeypatch):
    obj = SimpleNamespace(
        pk=10,
        registration=SimpleNamespace(pk=4),
    )
    button = SimpleNamespace(original=obj, href=None, html_attrs={})
    monkeypatch.setattr("aurora.registration.admin.record.reverse", lambda *_a, **_k: "/done/url")
    record_admin.receipt.func(record_admin, button)
    assert button.href == "/done/url"
    assert button.html_attrs["target"] == "_10"

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "aurora.registration.admin.record.reverse",
            lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        log = Mock()
        mp.setattr("aurora.registration.admin.record.logger.exception", log)
        record_admin.receipt.func(record_admin, button)
        log.assert_called_once()


def test_preview_and_inspect(record_admin, monkeypatch, rf):
    request = rf.get("/admin/")
    files_payload = {"file": "x"}
    record_admin.object = SimpleNamespace(files=SimpleNamespace(tobytes=lambda: json.dumps(files_payload).encode()))
    record_admin.get_common_context = Mock(return_value={"base": 1})

    monkeypatch.setattr("aurora.registration.admin.record.render", lambda *_a, **_k: HttpResponse("ok"))
    preview = record_admin.preview.func(record_admin, request, "1")
    assert preview.status_code == 200

    inspect = record_admin.inspect.func(record_admin, request, "1")
    assert inspect.status_code == 200


def test_decrypt_get_post_valid_invalid_and_exception(record_admin, monkeypatch, rf):
    request_get = rf.get("/admin/")
    request_post = rf.post("/admin/", data={"key": "k"})

    record_admin.object = SimpleNamespace(decrypt=lambda _k: {"a": 1})
    record_admin.get_common_context = Mock(return_value={"base": 1})
    record_admin.message_error_to_user = Mock()
    monkeypatch.setattr("aurora.registration.admin.record.render", lambda *_a, **_k: HttpResponse("ok"))

    response_get = record_admin.decrypt.func(record_admin, request_get, "1")
    assert response_get.status_code == 200

    form_valid = Mock(is_valid=Mock(return_value=True), cleaned_data={"key": "k"})
    monkeypatch.setattr("aurora.registration.admin.record.DecryptForm", lambda *_a, **_k: form_valid)
    response_post = record_admin.decrypt.func(record_admin, request_post, "1")
    assert response_post.status_code == 200

    form_invalid = Mock(is_valid=Mock(return_value=False))
    monkeypatch.setattr("aurora.registration.admin.record.DecryptForm", lambda *_a, **_k: form_invalid)
    response_invalid = record_admin.decrypt.func(record_admin, request_post, "1")
    assert response_invalid.status_code == 200

    def _raise(_k):
        raise RuntimeError("bad key")

    record_admin.object = SimpleNamespace(decrypt=_raise)
    monkeypatch.setattr("aurora.registration.admin.record.DecryptForm", lambda *_a, **_k: form_valid)
    response_error = record_admin.decrypt.func(record_admin, request_post, "1")
    assert response_error.status_code == 200
    record_admin.message_error_to_user.assert_called_once()


def test_permissions_follow_root_and_debug(record_admin, monkeypatch, rf):
    request = rf.get("/admin/")

    monkeypatch.setattr("aurora.registration.admin.record.settings.DEBUG", False)
    monkeypatch.setattr("aurora.registration.admin.record.is_root", lambda *_a, **_k: False)
    assert record_admin.get_readonly_fields(request) == record_admin.readonly_fields
    assert record_admin.has_view_permission(request) is False
    assert record_admin.has_add_permission(request) is False
    assert record_admin.has_change_permission(request) is False
    assert record_admin.has_delete_permission(request) is False

    monkeypatch.setattr("aurora.registration.admin.record.settings.DEBUG", True)
    assert record_admin.get_readonly_fields(request) == []
    assert record_admin.has_view_permission(request) is True
    assert record_admin.has_add_permission(request) is True
    assert record_admin.has_change_permission(request) is True
    assert record_admin.has_delete_permission(request) is True
