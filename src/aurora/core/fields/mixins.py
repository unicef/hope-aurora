from django.utils.translation import get_language

from aurora.core.utils import oneline
from aurora.state import state


class TailWindMixin:
    def __init__(self, attrs=None, **kwargs):
        attrs = {
            "class": "shadow appearance-none border rounded w-full py-2 px-3 my-1 cursor-pointer"
            "text-gray-700 leading-tight focus:outline-none focus:shadow-outline ",
            **(attrs or {}),
        }
        super().__init__(attrs=attrs, **kwargs)


class SmartWidgetMixin:
    def get_context(self, name, value, attrs):
        ret = super().get_context(name, value, attrs)
        ret["LANGUAGE_CODE"] = get_language()
        ret["request"] = state.request
        ret["user"] = state.request.user
        return ret


class SmartFieldMixin:
    NONE = None
    PRIMARY = 1
    BLOB = 2
    storage = PRIMARY

    def __init__(self, *args, **kwargs) -> None:
        self.flex_field = kwargs.pop("flex_field")
        self.smart_attrs = kwargs.pop("smart_attrs", kwargs.pop("smart", {}))
        self.field_attrs = kwargs.pop("field_attrs", {})
        self.data_attrs = kwargs.pop("data", {})
        self.widget_kwargs = kwargs.pop("widget_kwargs", {})
        self.smart_events = kwargs.pop("smart_events", {})
        self.datasource = kwargs.pop("datasource", None)
        super().__init__(*args, **kwargs)

    def is_stored(self):
        return self.storage in [self.PRIMARY, self.BLOB]

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        attrs.update({k: v for k, v in self.widget_kwargs.items() if v is not None})

        for k, v in self.smart_attrs.items():
            if k.startswith("data-") or k.startswith("on") and v:
                attrs[k] = v

        for k, v in self.widget_kwargs.items():
            if k.startswith("data-") or k.startswith("on") and v:
                attrs[k] = v

        for k, v in self.data_attrs.items():
            attrs[f"data-{k}"] = v

        if self.flex_field.validator:
            attrs["data-smart-validator"] = self.flex_field.validator.name

        if not self.flex_field.required:
            attrs.pop("required", "")
        attrs["data-flex-name"] = self.flex_field.name
        for attr in [
            "onblur",
            "onchange",
            "onkeyup",
        ]:
            if attr in self.smart_events and self.smart_events[attr]:
                attrs[attr] = oneline(self.smart_events[attr])

        for attr in [
            "onload",
        ]:
            if attr in self.smart_events and self.smart_events[attr]:
                attrs[f"data-{attr}"] = oneline(self.smart_events[attr])

        if validation := self.smart_events.get("validation", None):
            attrs["data-validation"] = oneline(validation)
        widget.smart_attrs = self.smart_attrs
        widget.flex_field = self.flex_field
        return attrs


class MultiValueWidgetMixin:
    def get_context(self, name, value, attrs):
        context = {
            "widget": {
                "name": name,
                "is_hidden": self.is_hidden,
                "required": self.is_required,
                "value": self.format_value(value),
                "attrs": self.build_attrs(self.attrs, attrs),
                "template_name": self.template_name,
            },
        }
        if self.is_localized:
            for widget in self.widgets:
                widget.is_localized = self.is_localized
        # value is a list/tuple of values, each corresponding to a widget
        # in self.widgets.
        if not isinstance(value, (list, tuple)):
            value = self.decompress(value)

        final_attrs = context["widget"]["attrs"]
        input_type = final_attrs.pop("type", None)
        id_ = final_attrs.get("id")
        subwidgets = []
        for i, (widget_name, widget) in enumerate(
                zip(self.widgets_names, self.widgets)
        ):
            if input_type is not None:
                widget.input_type = input_type
            widget_name = name + widget_name
            try:
                widget_value = value[i]
            except IndexError:
                widget_value = None
            if id_:
                widget_attrs = final_attrs.copy()
                widget_attrs["id"] = "%s_%s" % (id_, i)
            else:
                widget_attrs = final_attrs
            widget.flex_field = self.flex_field
            widget.smart_attrs = self.smart_attrs
            subwidgets.append(
                widget.get_context(widget_name, widget_value, widget_attrs)["widget"]
            )
        context["widget"]["subwidgets"] = subwidgets
        return context