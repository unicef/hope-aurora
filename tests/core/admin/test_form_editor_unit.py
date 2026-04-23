from types import SimpleNamespace

from django.forms import Media
from django.http import HttpResponse
from django.test import RequestFactory

from aurora.core.admin.form_editor import AdvancendAttrsMixin
from aurora.core.admin.form_editor import FormEditor
from aurora.core.admin.form_editor import get_initial


class DummyEditor:
    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs


class DummyAdvancedForm(AdvancendAttrsMixin, DummyEditor):
    pass


class DummyForm:
    valid = True
    errors_data = {}

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.errors = self.errors_data
        self.media = Media(js=["f.js"])

    def is_valid(self):
        return self.valid


class DummyPatchedForm:
    def __init__(self, data=None):
        self.data = data


def _make_request(method="GET", data=None):
    rf = RequestFactory()
    if method == "POST":
        req = rf.post("/", data=data or {})
    else:
        req = rf.get("/")
    req.user = SimpleNamespace(pk=7)
    return req


def _make_editor(request=None, flex_form=None):
    request = request or _make_request()
    modeladmin = SimpleNamespace(get_common_context=lambda req, pk: {"ctx": (req, pk)})
    editor = FormEditor(modeladmin, request, "11")
    editor.FORMS = {"frm": DummyForm, "events": DummyForm}
    editor.__dict__["flex_form"] = flex_form or SimpleNamespace(
        advanced={"frm": {"name": "X"}, "events": {"onload": "a();"}},
        get_form_class=lambda: DummyPatchedForm,
    )
    return editor


def test_advanced_attrs_mixin_consumes_form_kwarg():
    instance = DummyAdvancedForm(form="ff", other="x")
    assert instance.form == "ff"
    assert instance.kwargs == {"other": "x"}


def test_get_initial_uses_defaults_and_truthy_values(monkeypatch):
    from aurora.core.admin import form_editor as module

    monkeypatch.setattr(module, "DEFAULTS", {"frm": {"a": 1, "b": 2}})
    ff = SimpleNamespace(advanced={"frm": {"a": 0, "c": 3}})
    assert get_initial(ff, "frm") == {"a": 1, "b": 2, "c": 3}


def test_form_editor_flex_form_and_patched_form(monkeypatch):
    from aurora.core.admin import form_editor as module

    flex_form = SimpleNamespace(get_form_class=lambda: DummyPatchedForm)
    monkeypatch.setattr(module.FlexForm.objects, "get", lambda **_k: flex_form)
    editor = _make_editor()
    editor.__dict__.pop("flex_form")
    assert editor.flex_form is flex_form
    assert editor.patched_form is DummyPatchedForm
    assert editor.cache_key == "/editor/form/7/11/"


def test_get_forms_branches():
    editor = _make_editor(request=_make_request("GET"))
    data_forms = editor.get_forms(data={"frm-name": "A"})
    assert data_forms["frm"].args[0] == {"frm-name": "A"}

    post_editor = _make_editor(request=_make_request("POST", data={"x": "1"}))
    post_forms = post_editor.get_forms()
    assert post_forms["frm"].args[0]["x"] == "1"
    assert post_forms["frm"].kwargs["initial"]["name"] == "X"

    get_forms = editor.get_forms()
    assert "initial" in get_forms["frm"].kwargs
    assert get_forms["frm"].kwargs["prefix"] == "frm"


def test_is_valid_and_refresh_branches():
    editor = _make_editor(request=_make_request("POST", data={"csrfmiddlewaretoken": "t", "a": "1"}))
    DummyForm.valid = True
    response = editor.refresh()
    assert response.status_code == 200
    assert response.content == b'{"a": "1"}'

    DummyForm.valid = False
    DummyForm.errors_data = {"f": ["bad"]}
    response = editor.refresh()
    assert response.status_code == 400
    assert editor.errors["frm"] == {"f": ["bad"]}
    DummyForm.errors_data = {}


def test_get_context_get_post_and_render(monkeypatch):
    editor = _make_editor(request=_make_request("GET"))

    def fake_render(_request, _template, ctx, **_kwargs):
        return HttpResponse(str(sorted(ctx.keys())))

    monkeypatch.setattr("aurora.core.admin.form_editor.render", fake_render)
    forms = {"frm": DummyForm(prefix="frm"), "events": DummyForm(prefix="events")}
    monkeypatch.setattr(editor, "get_forms", lambda data=None: forms)

    get_resp = editor.get(editor.request, "11")
    assert get_resp.status_code == 200
    assert b"form_frm" in get_resp.content
    assert b"forms_media" in get_resp.content

    monkeypatch.setattr(editor, "is_valid", lambda: True)
    assert editor.post(editor.request, "11").status_code == 302
    monkeypatch.setattr(editor, "is_valid", lambda: False)
    assert editor.post(editor.request, "11") is None

    get_render = editor.render()
    assert get_render.status_code == 200

    editor.request = _make_request("POST", data={"x": "1"})
    post_render = editor.render()
    assert post_render.status_code == 200


def test_get_configuration():
    editor = _make_editor()
    response = editor.get_configuration()
    assert response.status_code == 200
    assert response.content == b"aaaa"
