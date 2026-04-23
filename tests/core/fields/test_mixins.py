from types import SimpleNamespace

from django import forms
from django.test import RequestFactory

from aurora.core.fields.mixins import MultiValueWidgetMixin
from aurora.core.fields.mixins import SmartFormField
from aurora.core.fields.mixins import SmartWidgetMixin
from aurora.core.fields.mixins import TailWindMixin
from aurora.state import state


class DummyTailWidget(TailWindMixin, forms.TextInput):
    pass


class DummySmartWidget(SmartWidgetMixin, forms.TextInput):
    pass


class DummyMultiWidget(MultiValueWidgetMixin, forms.MultiWidget):
    def __init__(self):
        widgets = (forms.TextInput(), forms.TextInput())
        super().__init__(widgets)
        self.widgets_names = ("_0", "_1")
        self.flex_field = SimpleNamespace(name="field_name")
        self.smart_attrs = {}

    def decompress(self, value):
        return [value, None]


def test_tailwind_mixin_adds_default_class():
    widget = DummyTailWidget()
    assert "aurora-field" in widget.attrs["class"]


def test_smart_widget_mixin_context_uses_state_request():
    req = RequestFactory().get("/")
    req.user = SimpleNamespace(username="u1")
    state.request = req
    widget = DummySmartWidget()
    ctx = widget.get_context("name", "value", {})
    assert ctx["LANGUAGE_CODE"]
    assert ctx["request"] is req
    assert ctx["user"] is req.user


def test_smart_form_field_widget_attrs_branches():
    flex_field = SimpleNamespace(
        validator=SimpleNamespace(name="v1"),
        required=False,
        name="my_field",
    )
    field = SmartFormField(
        flex_field=flex_field,
        required=True,
        widget=forms.TextInput(),
        smart_attrs={"data-x": "1", "onchange": "do()", "extra_classes": "a b"},
        widget_kwargs={"class": "input-class", "onblur": "go()"},
        data={"foo": "bar"},
        smart_events={"onkeyup": "x=1", "onload": "init()", "validation": "rule()"},
    )
    attrs = field.widget_attrs(field.widget)
    assert attrs["data-x"] == "1"
    assert attrs["onchange"] == "do()"
    assert attrs["onblur"] == "go()"
    assert attrs["data-foo"] == "bar"
    assert attrs["data-smart-validator"] == "v1"
    assert "required" not in attrs
    assert attrs["data-flex-name"] == "my_field"
    assert attrs["onkeyup"] == "x=1"
    assert attrs["data-onload"] == "init()"
    assert attrs["data-validation"] == "rule()"
    assert field.widget.flex_field is flex_field


def test_multi_value_widget_mixin_context_handles_decompress_and_missing_values():
    widget = DummyMultiWidget()
    ctx = widget.get_context("field", "value", {"id": "my-id", "type": "text"})
    subwidgets = ctx["widget"]["subwidgets"]
    assert len(subwidgets) == 2
    assert subwidgets[0]["attrs"]["id"] == "my-id_0"
    assert subwidgets[1]["attrs"]["id"] == "my-id_1"
