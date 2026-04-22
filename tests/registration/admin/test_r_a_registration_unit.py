import datetime
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect
from django.test import RequestFactory
from django.urls import reverse

from aurora.registration.admin.registration import RegistrationAdmin, can_export_data
from aurora.registration.models import Registration


@pytest.fixture
def registration_admin():
    return RegistrationAdmin(Registration, admin.site)


def test_can_export_data_checks_permission_or_root(monkeypatch):
    request = SimpleNamespace(user=SimpleNamespace(has_perm=Mock(return_value=True)))
    obj = SimpleNamespace(export_allowed=True)
    monkeypatch.setattr("aurora.registration.admin.registration.is_root", lambda *_args, **_kwargs: False)
    assert can_export_data(request, obj) is True

    request.user.has_perm.return_value = False
    monkeypatch.setattr("aurora.registration.admin.registration.is_root", lambda *_args, **_kwargs: True)
    assert can_export_data(request, obj) is True

    monkeypatch.setattr("aurora.registration.admin.registration.is_root", lambda *_args, **_kwargs: False)
    obj.export_allowed = False
    assert can_export_data(request, obj) is False


def test_get_list_display_hides_org_or_project(registration_admin):
    req = RequestFactory().get("/admin/")
    req.GET = {"project__organization__exact": "1"}
    display = registration_admin.get_list_display(req)
    assert "organization" not in display
    assert "project" in display

    req = RequestFactory().get("/admin/")
    req.GET = {}
    display = registration_admin.get_list_display(req)
    assert "project" not in display
    assert "organization" in display


def test_formfield_for_dbfield_styles_unique_fields(registration_admin):
    request = RequestFactory().get("/admin/")
    db_field = Registration._meta.get_field("unique_field_path")
    formfield = registration_admin.formfield_for_dbfield(db_field, request)
    assert formfield.widget.attrs["style"] == "width:80%"


def test_get_readonly_fields_extends_for_non_root(registration_admin, monkeypatch):
    request = RequestFactory().get("/admin/")
    request.user = SimpleNamespace(is_staff=True)
    obj = SimpleNamespace(pk=1)

    monkeypatch.setattr("aurora.registration.admin.registration.is_root", lambda *_args, **_kwargs: False)
    readonly = registration_admin.get_readonly_fields(request, obj)
    assert "slug" in readonly
    assert "export_allowed" in readonly
    assert "archived" in readonly

    monkeypatch.setattr("aurora.registration.admin.registration.is_root", lambda *_args, **_kwargs: True)
    readonly_root = registration_admin.get_readonly_fields(request, obj)
    assert "slug" not in readonly_root


def test_secure_and_admin_sync_show_inspect(registration_admin):
    assert registration_admin.secure(SimpleNamespace(public_key="key", encrypt_data=False)) is True
    assert registration_admin.secure(SimpleNamespace(public_key="", encrypt_data=True)) is True
    assert registration_admin.secure(SimpleNamespace(public_key="", encrypt_data=False)) is False
    assert registration_admin.admin_sync_show_inspect() is True


def test_redirect_helpers(registration_admin):
    request = RequestFactory().get("/admin/")
    obj = SimpleNamespace(
        slug="reg-slug",
        pk=11,
        project=SimpleNamespace(pk=7, organization=SimpleNamespace(slug="org-slug")),
    )
    registration_admin.get_object = Mock(return_value=obj)

    inspect_resp = registration_admin.inspect_data.func(registration_admin, request, "11")
    assert isinstance(inspect_resp, HttpResponseRedirect)
    assert inspect_resp.url == reverse("register-data", args=[obj.slug])

    records_resp = registration_admin.records.func(registration_admin, request, "11")
    assert records_resp.url == reverse("api:registration-records", args=[obj.pk])

    charts_resp = registration_admin.charts.func(registration_admin, request, "11")
    assert charts_resp.url == reverse("charts:monthly", args=[obj.project.organization.slug, obj.project.pk, "11"])

    collected_resp = registration_admin.view_collected_data.func(registration_admin, request, "11")
    assert collected_resp.url == f"{reverse('admin:registration_record_changelist')}?registration__exact=11"


def test_collect_calls_counter_collect(registration_admin, monkeypatch):
    called = {}

    class _CounterObjects:
        @staticmethod
        def collect(**kwargs):
            called["kwargs"] = kwargs

    class _Counter:
        objects = _CounterObjects()

    monkeypatch.setattr("aurora.counters.models.Counter", _Counter)
    request = RequestFactory().get("/admin/")
    registration_admin.collect.func(registration_admin, request, "55")
    assert called["kwargs"] == {"registrations": ["55"]}


def test_change_buttons_are_sorted_and_filtered(registration_admin, monkeypatch):
    h1 = SimpleNamespace(change_form=True, change_list=True, config={"order": 2})
    h2 = SimpleNamespace(change_form=None, change_list=None, config={"order": 1})
    h3 = SimpleNamespace(change_form=False, change_list=False, config={"order": 0})

    monkeypatch.setattr(
        "smart_admin.modeladmin.SmartModelAdmin.get_changeform_buttons",
        lambda *_args, **_kwargs: [h1, h2, h3],
    )
    buttons = registration_admin.get_changeform_buttons({})
    assert buttons == [h2, h1]

    registration_admin.extra_button_handlers = {"a": h1, "b": h2, "c": h3}
    cl_buttons = registration_admin.get_changelist_buttons({})
    assert cl_buttons == [h2, h1]


def test_archive_sets_archived_state_on_post(registration_admin, monkeypatch):
    request = RequestFactory().post("/admin/", data={"archive": "1"})
    reg = SimpleNamespace(end=None, archived=False, active=True, pk=77, save=Mock())
    ctx = {"original": reg, "clearable": False}
    monkeypatch.setattr(registration_admin, "get_common_context", lambda *_args, **_kwargs: ctx)
    monkeypatch.setattr("aurora.registration.admin.registration.render", lambda *_args, **_kwargs: HttpResponse("ok"))
    monkeypatch.setattr("aurora.registration.admin.registration.timezone.now", lambda: SimpleNamespace(date=lambda: 1))

    response = registration_admin.archive.func(registration_admin, request, "77")
    assert response.status_code == 200
    assert reg.archived is True
    assert reg.active is False
    reg.save.assert_called_once()


def test_archive_clear_sends_remove_records_task(registration_admin, monkeypatch):
    request = RequestFactory().post("/admin/", data={"clear": "1"})
    reg = SimpleNamespace(end=datetime.date(2026, 1, 1), archived=False, active=False, pk=88, save=Mock())
    ctx = {"original": reg, "clearable": True}
    remove_send = Mock()
    monkeypatch.setattr(registration_admin, "get_common_context", lambda *_args, **_kwargs: ctx)
    monkeypatch.setattr("aurora.registration.admin.registration.render", lambda *_args, **_kwargs: HttpResponse("ok"))
    monkeypatch.setattr("aurora.registration.admin.registration.remove_records.send", remove_send)
    monkeypatch.setattr("aurora.registration.admin.registration.timezone.now", lambda: datetime.datetime(2026, 1, 20))

    registration_admin.archive.func(registration_admin, request, "88")
    remove_send.assert_called_once_with(88)


def test_encryption_choice_variants(registration_admin):
    button = SimpleNamespace(
        context={"original": SimpleNamespace(public_key="pk", encrypt_data=False)},
        choices=[],
        config={},
    )
    registration_admin.encryption.func(registration_admin, button)
    assert button.choices == [registration_admin.removekey]

    button = SimpleNamespace(
        context={"original": SimpleNamespace(public_key="", encrypt_data=True)},
        choices=[],
        config={},
    )
    registration_admin.encryption.func(registration_admin, button)
    assert button.choices == [registration_admin.toggle_encryption]

    button = SimpleNamespace(
        context={"original": SimpleNamespace(public_key="", encrypt_data=False)},
        choices=[],
        config={},
    )
    registration_admin.encryption.func(registration_admin, button)
    assert button.choices == [registration_admin.generate_keys, registration_admin.toggle_encryption]


def test_toggle_encryption_and_removekey(registration_admin, monkeypatch):
    request = RequestFactory().post("/admin/", data={})
    obj = SimpleNamespace(encrypt_data=False, public_key="key", save=Mock())
    registration_admin.get_object = Mock(return_value=obj)
    registration_admin.toggle_encryption.func(registration_admin, request, "1")
    assert obj.encrypt_data is True

    registration_admin.get_common_context = Mock(return_value={"original": obj})
    registration_admin.message_user = Mock()
    registration_admin.log_change = Mock()
    response = registration_admin.removekey.func(registration_admin, request, "1")
    assert isinstance(response, HttpResponseRedirect)
    assert response.url == ".."
    assert obj.public_key == ""
    registration_admin.message_user.assert_called_once()
    registration_admin.log_change.assert_called_once()


def test_generate_keys_and_james_helpers(registration_admin, monkeypatch):
    request = RequestFactory().post("/admin/", data={})
    request_get = RequestFactory().get("/admin/")
    obj = SimpleNamespace(
        setup_encryption_keys=Mock(return_value=("priv", "pub")),
        flex_form=SimpleNamespace(get_form_class=Mock(return_value=type("X", (), {}))),
    )
    registration_admin.object = obj
    ctx = {"original": obj}
    registration_admin.get_common_context = Mock(return_value=ctx)

    render_calls = {}

    def _render(_req, _template, passed_ctx):
        render_calls["ctx"] = passed_ctx
        return HttpResponse("ok")

    monkeypatch.setattr("aurora.registration.admin.registration.render", _render)
    registration_admin.log_change = Mock()
    registration_admin.generate_keys.func(registration_admin, request, "1")
    assert render_calls["ctx"]["private_key"] == "priv"
    assert render_calls["ctx"]["public_key"] == "pub"

    registration_admin.get_object = Mock(return_value=obj)
    cache_get = Mock(side_effect=[None, "cached-value"])
    cache_set = Mock()
    monkeypatch.setattr("aurora.registration.admin.registration.cache.get", cache_get)
    monkeypatch.setattr("aurora.registration.admin.registration.cache.set", cache_set)
    monkeypatch.setattr("aurora.registration.admin.registration.get_system_cache_version", lambda: "v1")
    monkeypatch.setattr(
        "aurora.registration.admin.registration.build_form_fake_data",
        lambda *_args, **_kwargs: {"a": 1},
    )

    miss_resp = registration_admin.james_fake_data.func(registration_admin, request_get, "5")
    hit_resp = registration_admin.james_fake_data.func(registration_admin, request_get, "5")
    assert '"a": 1' in miss_resp.content.decode()
    assert hit_resp.content.decode() == "cached-value"
    cache_set.assert_called_once()


def test_james_editor_get_and_post(registration_admin, monkeypatch):
    original = SimpleNamespace()
    registration_admin.get_common_context = Mock(return_value={"original": original})
    monkeypatch.setattr("aurora.registration.admin.registration.get_system_cache_version", lambda: "v1")
    monkeypatch.setattr("aurora.registration.admin.registration.cache.get", lambda *_args, **_kwargs: "cached-json")
    cache_set = Mock()
    monkeypatch.setattr("aurora.registration.admin.registration.cache.set", cache_set)
    monkeypatch.setattr("aurora.registration.admin.registration.render", lambda *_args, **_kwargs: HttpResponse("ok"))

    form = Mock()
    form.is_valid.return_value = True
    form.cleaned_data = {"data": "{}"}
    form.save = Mock()
    monkeypatch.setattr("aurora.registration.admin.registration.JamesForm", lambda *args, **kwargs: form)

    get_resp = registration_admin.james_editor.func(registration_admin, RequestFactory().get("/admin/"), "6")
    assert get_resp.status_code == 200

    post_resp = registration_admin.james_editor.func(
        registration_admin,
        RequestFactory().post("/admin/", data={"data": "{}"}),
        "6",
    )
    assert isinstance(post_resp, HttpResponseRedirect)
    cache_set.assert_called_once()


def test_choice_sets_for_admin_and_data(registration_admin, monkeypatch):
    button = SimpleNamespace(
        choices=[],
        context={"request": RequestFactory().get("/"), "original": SimpleNamespace()},
        original=SimpleNamespace(),
        config={},
    )
    registration_admin.admin.func(registration_admin, button)
    assert registration_admin.james_editor in button.choices
    assert registration_admin.debug in button.choices

    monkeypatch.setattr(
        "aurora.registration.admin.registration.can_export_data",
        lambda *_args, **_kwargs: True,
    )
    data_button = SimpleNamespace(
        choices=[],
        context={"request": RequestFactory().get("/")},
        original=SimpleNamespace(),
        config={},
    )
    registration_admin.data.func(registration_admin, data_button)
    assert registration_admin.export_as_csv in data_button.choices


def test_invalidate_cache_saves_object(registration_admin):
    request = RequestFactory().get("/admin/")
    obj = SimpleNamespace(save=Mock())
    registration_admin.get_object = Mock(return_value=obj)
    registration_admin.invalidate_cache.func(registration_admin, request, "1")
    obj.save.assert_called_once()


def test_inspect_renders_template(registration_admin, monkeypatch):
    request = RequestFactory().get("/admin/")
    registration_admin.get_common_context = Mock(return_value={"original": SimpleNamespace()})
    monkeypatch.setattr("aurora.registration.admin.registration.render", lambda *_args, **_kwargs: HttpResponse("ok"))
    response = registration_admin.inspect.func(registration_admin, request, "1")
    assert response.status_code == 200


def test_debug_get_and_invalid_post(registration_admin, monkeypatch):
    request_get = RequestFactory().get("/admin/")
    request_post = RequestFactory().post("/admin/", data={})
    registration_admin.get_common_context = Mock(return_value={"original": SimpleNamespace()})
    monkeypatch.setattr("aurora.registration.admin.registration.render", lambda *_args, **_kwargs: HttpResponse("ok"))

    form_invalid = Mock()
    form_invalid.is_valid.return_value = False
    monkeypatch.setattr("aurora.registration.admin.registration.DebugForm", lambda *args, **kwargs: form_invalid)
    assert registration_admin.debug.func(registration_admin, request_get, "1").status_code == 200
    assert registration_admin.debug.func(registration_admin, request_post, "1").status_code == 200


def test_debug_post_valid_populates_results(registration_admin, monkeypatch):
    request = RequestFactory().post("/admin/", data={"search": "foo"})
    registration_admin.get_common_context = Mock(return_value={"original": SimpleNamespace()})
    monkeypatch.setattr("aurora.registration.admin.registration.render", lambda *_args, **_kwargs: HttpResponse("ok"))

    form = Mock()
    form.is_valid.return_value = True
    form.cleaned_data = {"search": "foo"}
    monkeypatch.setattr("aurora.registration.admin.registration.DebugForm", lambda *args, **kwargs: form)

    row = SimpleNamespace(get_admin_change_url=lambda: "/admin/x/")
    row.__str__ = lambda self=row: "row"
    qs = [row]
    monkeypatch.setattr(
        "aurora.registration.admin.registration.Validator.objects.filter",
        lambda **kwargs: SimpleNamespace(defer=lambda *_a: qs),
    )
    monkeypatch.setattr(
        "aurora.registration.admin.registration.FormSet.objects.filter",
        lambda **kwargs: SimpleNamespace(defer=lambda *_a: qs),
    )
    monkeypatch.setattr(
        "aurora.registration.admin.registration.FlexForm.objects.filter",
        lambda **kwargs: SimpleNamespace(defer=lambda *_a: qs),
    )
    monkeypatch.setattr(
        "aurora.registration.admin.registration.FlexFormField.objects.filter",
        lambda **kwargs: SimpleNamespace(defer=lambda *_a: qs),
    )

    assert registration_admin.debug.func(registration_admin, request, "1").status_code == 200


def test_export_as_csv_handles_too_many_records(registration_admin, monkeypatch):
    request = RequestFactory().post("/admin/", data={})
    registration_admin.get_common_context = Mock(return_value={"original": SimpleNamespace(slug="slug1")})
    registration_admin.message_user = Mock()
    monkeypatch.setattr("aurora.registration.admin.registration.render", lambda *_args, **_kwargs: HttpResponse("ok"))

    form = Mock(
        is_valid=Mock(return_value=True),
        cleaned_data={"filters": ({}, {}), "include": {"id"}, "exclude": set()},
    )
    opts_form = Mock(is_valid=Mock(return_value=True), cleaned_data={"header": True})
    fmt_form = Mock(is_valid=Mock(return_value=True), cleaned_data={})

    class _OptsForm:
        defaults = {}

        def __new__(cls, *args, **kwargs):
            return opts_form

    class _FmtForm:
        defaults = {}

        def __new__(cls, *args, **kwargs):
            return fmt_form

    monkeypatch.setattr("aurora.registration.admin.registration.RegistrationExportForm", lambda *args, **kwargs: form)
    monkeypatch.setattr("aurora.registration.admin.registration.CSVOptionsForm", _OptsForm)
    monkeypatch.setattr("aurora.registration.admin.registration.DateFormatsForm", _FmtForm)

    qs = SimpleNamespace(
        defer=lambda *_a: qs,
        filter=lambda **_k: qs,
        exclude=lambda **_k: qs,
        values=lambda *_a: qs,
        count=lambda: 5000,
    )
    monkeypatch.setattr("aurora.registration.admin.registration.Record.objects.filter", lambda **_k: qs)

    response = registration_admin.export_as_csv.func(registration_admin, request, "1")
    assert response.status_code == 200
    registration_admin.message_user.assert_called()


def test_create_custom_template_post_and_get(registration_admin, monkeypatch):
    req_get = RequestFactory().get("/admin/")
    req_post = RequestFactory().post("/admin/", data={"locale": "-"})
    original = SimpleNamespace(locale="en-us", slug="reg-1")
    registration_admin.get_common_context = Mock(return_value={"original": original})
    monkeypatch.setattr("aurora.registration.admin.registration.render", lambda *_args, **_kwargs: HttpResponse("ok"))

    form_get = Mock()
    form_post = Mock(is_valid=Mock(return_value=True), cleaned_data={"locale": "-"})
    monkeypatch.setattr(
        "aurora.registration.admin.registration.TemplateForm",
        lambda *args, **kwargs: form_post if args else form_get,
    )
    source = SimpleNamespace(template=SimpleNamespace(source="tmpl", name="source-name"))
    monkeypatch.setattr("aurora.registration.admin.registration.select_template", lambda *_a, **_k: source)
    monkeypatch.setattr(
        "dbtemplates.models.Template.objects.get_or_create",
        lambda **_k: (SimpleNamespace(name="x"), True),
    )

    assert registration_admin.create_custom_template.func(registration_admin, req_get, "1").status_code == 200
    assert registration_admin.create_custom_template.func(registration_admin, req_post, "1").status_code == 200


def test_prepare_translation_export_and_invalid_locale(registration_admin, monkeypatch):
    original = SimpleNamespace(name="Reg Name", locales=["en-us"])
    registration_admin.get_common_context = Mock(return_value={"original": original})
    registration_admin.message_user = Mock()
    monkeypatch.setattr("aurora.registration.admin.registration.render", lambda *_args, **_kwargs: HttpResponse("ok"))

    # Invalid locale in "create" branch
    req_create = RequestFactory().post("/admin/", data={"create": "1"})
    req_create.user = SimpleNamespace(pk=1)
    req_create.session = SimpleNamespace(session_key="sess")
    form_create = Mock(is_valid=Mock(return_value=True), cleaned_data={"locale": "it-it"})
    con = SimpleNamespace(delete=Mock(), lrange=Mock(return_value=[]))
    monkeypatch.setattr("aurora.registration.admin.registration.TranslationForm", lambda *args, **kwargs: form_create)
    monkeypatch.setattr("aurora.registration.admin.registration.get_redis_connection", lambda *_a, **_k: con)
    response = registration_admin.prepare_translation.func(registration_admin, req_create, "1")
    assert isinstance(response, HttpResponseRedirect)

    # Export branch
    req_export = RequestFactory().post(
        "/admin/",
        data={"export": "1", "selection": ["1"], "language_code": "en-us", "msgid_1": "Line1\nLine2"},
    )
    req_export.user = SimpleNamespace(pk=1)
    req_export.session = SimpleNamespace(session_key="sess")
    response = registration_admin.prepare_translation.func(registration_admin, req_export, "1")
    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"


def test_create_translation_get_and_invalid_post(registration_admin, monkeypatch):
    request_get = RequestFactory().get("/admin/")
    request_post = RequestFactory().post("/admin/", data={})
    registration_admin.get_common_context = Mock(return_value={"original": SimpleNamespace(slug="reg1", version=1)})
    monkeypatch.setattr("aurora.registration.admin.registration.render", lambda *_args, **_kwargs: HttpResponse("ok"))

    invalid_form = Mock(is_valid=Mock(return_value=False))
    monkeypatch.setattr("aurora.i18n.forms.LanguageForm", lambda *args, **kwargs: invalid_form)

    assert registration_admin.create_translation.func(registration_admin, request_get, "1").status_code == 200
    assert registration_admin.create_translation.func(registration_admin, request_post, "1").status_code == 200
