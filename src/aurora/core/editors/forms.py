from django_regex.forms import RegexFormField
from typing import Dict, List

from django import forms

from aurora.core.compat import StrategyFormField, JsRegexEditor
from aurora.core.fields.widgets import JavascriptEditor
from aurora.core.fields.widgets.mixins import TailWindMixin
from aurora.core.models import Section
from aurora.core.registry import field_registry


class CustomAttrsForm(forms.Form):
    pass
    # SECTIONS_MAP: Dict[Section, List] = dict(field=[], widget=[], smart=[], css=[], custom=[], data=[])


class AdvancendAttrsForm(forms.Form):
    title = None
    SECTIONS_MAP: Dict[Section, List] = dict(field=[], widget=[], smart=[], css=[], custom=[], data=[])

    def __init__(self, *args, **kwargs):
        self.field = kwargs.pop("field", None)
        self.prefix = kwargs.get("prefix")
        self.cleaned_data = {}
        self.title = self.title or self.__class__.__name__
        initial = self.extract_initials()
        # initial.update(**self.extract_custom())
        kwargs["initial"] = initial
        super().__init__(*args, **kwargs)

    def get_section(self, section: Section):
        targets = self.SECTIONS_MAP.get(section, [])
        return {k: v for k, v in self.cleaned_data.items() if k in targets}

    def extract_initials(self):
        # if self.SECTION:
        #     ret = self.field.advanced.get(self.SECTION, {})
        #     for name, __ in self.fields.items():
        #         ret[name] = getattr(self.field, name)
        # else:
        ret = {}
        for section, field_names in self.SECTIONS_MAP.items():
            if section == "field":
                for field_name in field_names:
                    ret[field_name] = getattr(self.field, field_name, "")
            else:
                for field_name in field_names:
                    ret[field_name] = self.field.advanced.get(section, {}).get(field_name, "")
        # for name, __ in self.base_fields.items():
        #     if name not in ret:
        #         ret[name] = getattr(self.field, name, "")
        return ret

    #
    # def extract_custom(self):
    #     ret = {}
    #     for section, fields in self.EXTRA_MAP.items():
    #         for fld in fields:
    #             ret[fld] = self.field.advanced.get(section, {}).get(fld, None)
    #     return ret


class AdvancedForm(AdvancendAttrsForm):
    SECTIONS_MAP = {
        "widget": ["value", "placeholder"],
        "smart": ["description", "hint"],
    }
    value = forms.CharField(label="default", required=False, help_text="default value for the field")
    placeholder = forms.CharField(required=False, help_text="placeholder for the input")
    description = forms.CharField(required=False, widget=forms.Textarea, help_text="Text to display below the input")
    hint = forms.CharField(required=False, widget=forms.Textarea, help_text="Text to display above the input")

    class Meta:
        title = "Advanced"
        help = ""


class CustomForm(AdvancendAttrsForm):
    def __init__(self, *args, **kwargs):
        from aurora.core.editors.configs import fields_config

        super().__init__(*args, **kwargs)
        self.custom = None
        if extra := fields_config.get(self.field.field_type, None):
            self.custom = extra()
            for name, field in self.custom.fields.items():
                self.fields[name] = field
                self.SECTIONS_MAP["custom"].append(name)

    class Meta:
        title = "Custom"
        help = ""

    def get_section(self, section: Section):
        if section == "custom" and self.custom:
            # targets = self.custom.SECTIONS_MAP.get(section, [])
            return {k: v for k, v in self.cleaned_data.items()}
        return {}


class FlexFieldAttributesForm(AdvancendAttrsForm):
    SECTIONS_MAP = {
        "field": ["field_type", "label", "required", "enabled"],
        "smart": ["visible"],
    }
    field_type = StrategyFormField(registry=field_registry)
    label = forms.CharField()
    required = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    enabled = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    visible = forms.BooleanField(required=False, help_text="Hide/Show field", initial=True)

    # choices = forms.JSONField(required=False, initial=[])
    # description = forms.CharField(required=False, help_text="Text to display below the input")
    # hint = forms.CharField(required=False, help_text="Text to display above the input")

    # def __init__(self, *args, **kwargs):
    # kwargs["instance"] = kwargs["field"]
    # super().__init__(*args, **kwargs)

    class Meta:
        # model = FlexFormField
        # fields = ("field_type", "label", "required", "enabled")
        title = "General"
        help = ""


class ValidationForm(AdvancendAttrsForm):
    SECTIONS_MAP = {
        "widget": ["title", "pattern"],
    }
    title = forms.CharField(label="Tooltip", required=False, help_text="")
    pattern = RegexFormField(label="Regex", required=False, help_text="", widget=JsRegexEditor)

    # validation = RegexFormField(label="Regex", required=False, help_text="", widget=JsRegexEditor)
    #         if self.registration.unique_field_path and not kwargs.get("unique_field", None):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        # model = FlexFormField
        # fields = ("regex", "title", "validation")
        title = "Validation"
        help = ""


class CssForm(AdvancendAttrsForm):
    SECTIONS_MAP = {"css": ["input", "label", "fieldset", "description", "hint"]}
    input = forms.CharField(required=False, initial=TailWindMixin.default_class)
    label = forms.CharField(required=False, initial="block uppercase tracking-wide text-gray-700 font-bold mb-2")
    fieldset = forms.CharField(required=False, help_text="")
    description = forms.CharField(required=False, help_text="")
    hint = forms.CharField(required=False, help_text="")

    class Meta:
        title = "Css"
        help = ""


class EventForm(AdvancendAttrsForm):
    SECTIONS_MAP = {
        "field": [],
        "widget": ["onchange", "onblur", "onkeyup", "onfocus"],
        "data": ["onload", "validation"],
    }

    onchange = forms.CharField(widget=JavascriptEditor(toolbar=True), required=False)
    onblur = forms.CharField(widget=JavascriptEditor(toolbar=True), required=False)
    onkeyup = forms.CharField(widget=JavascriptEditor(toolbar=True), required=False)
    onload = forms.CharField(widget=JavascriptEditor(toolbar=True), required=False)
    onfocus = forms.CharField(widget=JavascriptEditor(toolbar=True), required=False)

    validation = forms.CharField(widget=JavascriptEditor(toolbar=True), required=False)

    # init = forms.CharField(widget=JavascriptEditor(toolbar=True), required=False)

    class Meta:
        title = "Events"
        help = ""
