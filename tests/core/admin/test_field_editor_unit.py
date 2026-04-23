from types import SimpleNamespace

from django import forms
from django.http import HttpResponse
from django.test import RequestFactory

from aurora.core.admin.field_editor import AdvancendAttrsMixin
from aurora.core.admin.field_editor import FieldEditor
from aurora.core.admin.field_editor import get_datasources
from aurora.core.admin.field_editor import get_initial


class DummyBase:
    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs


class DummyAdvanced(AdvancendAttrsMixin, DummyBase):
    pass


class DummyConfigForm:
    valid = True
    cleaned_data = {"k": "v"}
    errors = {"e": ["x"]}

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.media = forms.Media(js=["m.js"])

    def is_valid(self):
        return self.valid


def _request(method="GET", data=None):
    rf = RequestFactory()
    req = rf.post("/", data=data or {}) if method == "POST" else rf.get("/")
    req.user = SimpleNamespace(pk=3)
    return req


def _field():
    return SimpleNamespace(
        field_type="CharField",
        name="myfield",
        advanced={"css": {"label": "L"}, "smart": {"visible": True}},
        get_instance=lambda: forms.CharField(required=False),
        get_default_value=lambda: "def",
        save=lambda: None,
    )


def _editor(monkeypatch, request=None):
    request = request or _request()
    modeladmin = SimpleNamespace(get_common_context=lambda req, pk: {"base": (req, pk)})
    fld = _field()
    monkeypatch.setattr(
        "aurora.core.admin.field_editor.FlexFormField.objects.get",
        lambda **_k: fld,
    )
    editor = FieldEditor(modeladmin, request, "9")
    editor.FORMS = {
        "field": DummyConfigForm,
        "widget": DummyConfigForm,
    }
    return editor, fld


def test_advanced_attrs_and_initial_helpers(monkeypatch):
    instance = DummyAdvanced(field=SimpleNamespace(advanced={"x": {"a": 1}}), prefix="x")
    assert instance.field.advanced["x"]["a"] == 1
    assert instance.initial == {"a": 1}

    from aurora.core.admin import field_editor as module

    monkeypatch.setattr(module, "DEFAULTS", {"css": {"label": "d", "question": "q"}})
    assert get_initial(SimpleNamespace(advanced={"css": {"label": "", "x": "1"}}), "css") == {
        "label": "d",
        "question": "q",
        "x": "1",
    }


def test_get_datasources(monkeypatch):
    class _Values:
        def values_list(self, *_a, **_k):
            return ["ds1", "ds2"]

    monkeypatch.setattr("aurora.core.admin.field_editor.OptionSet.objects.order_by", lambda *_a: _Values())
    assert get_datasources() == [("", ""), ("ds1", "ds1"), ("ds2", "ds2")]


def test_get_forms_and_refresh(monkeypatch):
    editor, _ = _editor(monkeypatch, request=_request("POST", {"csrfmiddlewaretoken": "t", "a": "1"}))
    forms_map = editor.get_forms()
    assert forms_map["field"].args[0]["a"] == "1"

    DummyConfigForm.valid = True
    response = editor.refresh()
    assert response.status_code == 200
    assert response.content == b'{"a": "1"}'

    DummyConfigForm.valid = False
    response = editor.refresh()
    assert response.status_code == 200
    assert b"field" in response.content


def test_patched_field_uses_cached_config(monkeypatch):
    editor, fld = _editor(monkeypatch)
    editor.__dict__.pop("patched_field", None)

    field_form = DummyConfigForm()
    field_form.cleaned_data = {"name": "changed"}
    other_form = DummyConfigForm()
    other_form.cleaned_data = {"visible": False}

    monkeypatch.setattr("aurora.core.admin.field_editor.cache.get", lambda *_a, **_k: {"x": 1})
    monkeypatch.setattr(editor, "get_forms", lambda data=None: {"field": field_form, "smart": other_form})
    monkeypatch.setattr("aurora.core.admin.field_editor.merge_data", lambda a, b: {**a, **b})
    DummyConfigForm.valid = True

    patched = editor.patched_field
    assert patched.name == "changed"
    assert patched.advanced["smart"] == {"visible": False}


def test_get_configuration_get_post_and_render(monkeypatch):
    editor, fld = _editor(monkeypatch)

    monkeypatch.setattr("aurora.core.admin.field_editor.render", lambda *_a, **_k: HttpResponse("ok"))
    monkeypatch.setattr(
        editor,
        "get_forms",
        lambda data=None: {"field": DummyConfigForm(), "widget": DummyConfigForm()},
    )

    editor.__dict__["patched_field"] = fld
    cfg = editor.get_configuration()
    assert cfg.status_code == 200
    assert b'"css"' in cfg.content

    get_resp = editor.get(editor.request, "9")
    assert get_resp.status_code == 200

    post_editor, _ = _editor(monkeypatch, request=_request("POST", {"myfield": "X"}))
    monkeypatch.setattr("aurora.core.admin.field_editor.render", lambda *_a, **_k: HttpResponse("ok-post"))

    def _always_valid(self):
        self.cleaned_data = {"myfield": "X"}
        return True

    monkeypatch.setattr("aurora.core.forms.FlexFormBaseForm.is_valid", _always_valid)
    render_resp = post_editor.render()
    assert render_resp.status_code == 200

    save_calls = []
    post_editor.__dict__["patched_field"] = SimpleNamespace(save=lambda: save_calls.append(1))
    monkeypatch.setattr(
        post_editor,
        "get_forms",
        lambda data=None: {"field": DummyConfigForm(), "widget": DummyConfigForm()},
    )
    DummyConfigForm.valid = True
    assert post_editor.post(post_editor.request, "9").status_code == 302
    assert save_calls == [1]

    DummyConfigForm.valid = False
    assert post_editor.post(post_editor.request, "9") is None
