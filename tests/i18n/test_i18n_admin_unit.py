from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.test import RequestFactory

from aurora.i18n.admin import MessageAdmin
from aurora.i18n.models import Message


@pytest.fixture
def message_admin():
    return MessageAdmin(Message, admin.site)


def test_approve_and_rehash(message_admin):
    request = RequestFactory().post("/admin/")
    message_admin.message_user = Mock()

    qs = SimpleNamespace(update=lambda **_k: 3)
    message_admin.approve(request, qs)
    message_admin.message_user.assert_called_once()

    message_admin.message_user.reset_mock()
    m1 = SimpleNamespace(save=Mock())
    m2 = SimpleNamespace(save=Mock())
    message_admin.rehash(request, SimpleNamespace(all=lambda: [m1, m2]))
    m1.save.assert_called_once()
    m2.save.assert_called_once()
    message_admin.message_user.assert_called_once()


def test_get_readonly_fields_branch(message_admin):
    request = RequestFactory().get("/admin/")
    assert message_admin.get_readonly_fields(request, obj=None) == message_admin.readonly_fields
    assert "msgid" in message_admin.get_readonly_fields(request, obj=SimpleNamespace())


def test_get_or_create_get_redirect(message_admin):
    request = RequestFactory().get("/admin/")
    response = message_admin.get_or_create.func(message_admin, request)
    assert isinstance(response, HttpResponseRedirect)


@pytest.mark.django_db
def test_get_or_create_post_found_and_create(message_admin):
    request = RequestFactory().post("/admin/", data={"msgid": "hello", "lang": "en-us"})
    message_admin.message_user = Mock()
    existing = Message.objects.create(msgid="hello", msgstr="hello", locale="en-us")
    response = message_admin.get_or_create.func(message_admin, request)
    assert response.status_code == 302
    assert str(existing.pk) in response.url

    request = RequestFactory().post("/admin/", data={"msgid": "new-msg", "lang": "en-us"})
    response = message_admin.get_or_create.func(message_admin, request)
    assert response.status_code == 302


def test_siblings_redirect(message_admin):
    request = RequestFactory().get("/admin/")
    message_admin.get_object = lambda *_a, **_k: SimpleNamespace(msgcode="abc")
    response = message_admin.siblings.func(message_admin, request, "1")
    assert isinstance(response, HttpResponseRedirect)
    assert "msgcode__exact=abc" in response.url


def test_create_translation_single_invalid_form(message_admin, monkeypatch):
    request = RequestFactory().post("/admin/", data={})
    message_admin.get_common_context = lambda *_a, **_k: {"original": SimpleNamespace(msgid="m1")}
    monkeypatch.setattr("aurora.i18n.admin.render", lambda *_a, **_k: SimpleNamespace(status_code=200))

    invalid = Mock()
    invalid.is_valid.return_value = False
    monkeypatch.setattr("aurora.i18n.admin.LanguageForm", lambda *_a, **_k: invalid)
    response = message_admin.create_translation_single.func(message_admin, request, "1")
    assert response.status_code == 200


def test_create_translations_invalid_form(message_admin, monkeypatch):
    request = RequestFactory().post("/admin/", data={})
    message_admin.get_common_context = lambda *_a, **_k: {}
    monkeypatch.setattr("aurora.i18n.admin.render", lambda *_a, **_k: SimpleNamespace(status_code=200))
    invalid = Mock()
    invalid.is_valid.return_value = False
    monkeypatch.setattr("aurora.i18n.admin.LanguageForm", lambda *_a, **_k: invalid)
    response = message_admin.create_translations.func(message_admin, request)
    assert response.status_code == 200


def test_import_translations_get(message_admin, monkeypatch):
    request = RequestFactory().get("/admin/")
    message_admin.get_common_context = lambda *_a, **_k: {"pre": {}, "post": {}}
    monkeypatch.setattr("aurora.i18n.admin.render", lambda *_a, **_k: SimpleNamespace(status_code=200))
    response = message_admin.import_translations.func(message_admin, request)
    assert response.status_code == 200


def test_import_translations_save_branch(message_admin, monkeypatch):
    from aurora.state import state
    from contextlib import nullcontext

    request = RequestFactory().post("/admin/", data={"save": "1", "selection": ["msg-1"]})
    request.user = SimpleNamespace(pk=1)
    request.session = SimpleNamespace(session_key="sess")
    state.timestamp = "ts"

    message_admin.get_common_context = lambda *_a, **_k: {"pre": {}, "post": {}}
    message_admin.message_user = Mock()
    monkeypatch.setattr("aurora.i18n.admin.atomic", lambda: nullcontext())
    monkeypatch.setattr(
        "aurora.i18n.admin.cache.get",
        lambda *_a, **_k: {
            "language_code": "en-us",
            "messages": [
                [1, {"msgid": "msg-1", "msgstr": "Text 1"}],
                [2, {"msgid": "msg-2", "msgstr": "Text 2"}],
            ],
        },
    )
    monkeypatch.setattr(
        "aurora.i18n.admin.Message.objects.update_or_create",
        lambda **_k: (SimpleNamespace(pk=10), True),
    )

    response = message_admin.import_translations.func(message_admin, request)
    assert isinstance(response, HttpResponseRedirect)
    assert "locale__exact=en-us" in response.url


def test_import_translations_import_branch_large_file(message_admin, monkeypatch):
    from aurora.state import state

    request = RequestFactory().post("/admin/", data={"import": "1"})
    request.user = SimpleNamespace(pk=1)
    request.session = SimpleNamespace(session_key="sess")
    state.timestamp = "ts"

    message_admin.get_common_context = lambda *_a, **_k: {"pre": {}, "post": {}, "rows": []}
    message_admin.message_user = Mock()
    monkeypatch.setattr("aurora.i18n.admin.render", lambda *_a, **_k: SimpleNamespace(status_code=200))

    csv_file = SimpleNamespace(multiple_chunks=lambda: True, size=1200)
    form = Mock()
    form.is_valid.return_value = True
    form.cleaned_data = {"csv_file": csv_file, "locale": "en-us"}
    monkeypatch.setattr("aurora.i18n.admin.ImportLanguageForm", lambda *_a, **_k: form)

    opts_form = Mock()
    opts_form.is_valid.return_value = True
    opts_form.cleaned_data = {"header": False}
    monkeypatch.setattr("aurora.i18n.admin.CSVOptionsForm", lambda *_a, **_k: opts_form)

    response = message_admin.import_translations.func(message_admin, request)
    assert response.status_code == 200
    message_admin.message_user.assert_called()


def test_check_orphans_post_valid(message_admin, monkeypatch):
    request = RequestFactory().post("/admin/", data={"locale": "it-it"})
    message_admin.get_common_context = lambda *_a, **_k: {"pre": {}, "post": {}}
    monkeypatch.setattr("aurora.i18n.admin.render", lambda *_a, **_k: SimpleNamespace(status_code=200))

    form = Mock()
    form.is_valid.return_value = True
    form.cleaned_data = {"locale": "it-it"}
    monkeypatch.setattr("aurora.i18n.admin.LanguageForm", lambda *_a, **_k: form)
    monkeypatch.setattr("aurora.i18n.admin.FlexForm.objects.all", list)
    monkeypatch.setattr("aurora.i18n.admin.translator.activate", lambda *_a, **_k: None)
    monkeypatch.setattr("aurora.i18n.admin.translation.activate", lambda *_a, **_k: None)
    monkeypatch.setattr("aurora.i18n.admin.Message.objects.update", lambda **_k: None)
    monkeypatch.setattr("aurora.i18n.admin.Message.objects.all", lambda: SimpleNamespace(count=lambda: 10))
    monkeypatch.setattr("aurora.i18n.admin.Message.objects.filter", lambda **_k: SimpleNamespace(count=lambda: 2))

    response = message_admin.check_orphans.func(message_admin, request)
    assert response.status_code == 200


def test_create_translation_single_success_and_error(message_admin):
    request = RequestFactory().post("/admin/", data={"locale": "it-it"})
    message_admin.message_user = Mock()
    message_admin.message_error_to_user = Mock()

    original = SimpleNamespace(
        msgid="msgid-1",
        update_or_create_translation=lambda *_a, **_k: (SimpleNamespace(pk=5), True),
    )
    message_admin.get_common_context = lambda *_a, **_k: {"original": original}
    form = Mock()
    form.is_valid.return_value = True
    form.cleaned_data = {"locale": "it-it"}

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("aurora.i18n.admin.LanguageForm", lambda *_a, **_k: form)
        response = message_admin.create_translation_single.func(message_admin, request, "1")
        assert isinstance(response, HttpResponseRedirect)

    broken = SimpleNamespace(
        msgid="msgid-2",
        update_or_create_translation=lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    message_admin.get_common_context = lambda *_a, **_k: {"original": broken}
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("aurora.i18n.admin.LanguageForm", lambda *_a, **_k: form)
        response = message_admin.create_translation_single.func(message_admin, request, "1")
        assert isinstance(response, HttpResponseRedirect)
        message_admin.message_error_to_user.assert_called_once()
