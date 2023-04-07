from django.core.exceptions import ValidationError
from django_regex.forms import RegexFormField
from unittest.mock import Mock

import logging

import json
from django.conf import settings
from strategy_field.utils import fqn
from typing import Dict, Literal, List, Tuple

from django import forms
from django.core.cache import caches
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.template import Context, Template
from django.utils.functional import cached_property

from aurora.core.compat import JsRegexEditor, StrategyFormField
from aurora.core.fields.configs import fields_config
from aurora.core.fields.widgets import JavascriptEditor
from aurora.core.fields.widgets.mixins import TailWindMixin
from aurora.core.forms import VersionMedia, FlexFormBaseForm
from aurora.core.models import FlexFormField, OptionSet
from aurora.core.registry import field_registry
from aurora.core.utils import merge_data

logger = logging.getLogger(__name__)
cache = caches["default"]

# field: django.Field attrs
# widget: django.Widget attrs
# css: HTML class attributes
# custom: specific for each field type
# smart: Extra Aurora attributes. W
# data: Added to input element as data-<name>. Used internally

Section = Literal["field", "widget", "smart", "css", "custom", "data"]
Sections = Tuple[Section, ...]


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
        super().__init__(*args, **kwargs)
        if extra := fields_config.get(self.field.field_type, None):
            estra_form = extra()
            for name, field in estra_form.fields.items():
                self.fields[name] = field
                self.SECTIONS_MAP["custom"].append(name)

    class Meta:
        title = "Custom"
        help = ""


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        # model = FlexFormField
        # fields = ("regex", "title", "validation")
        title = "Validation"
        help = ""


def get_datasources():
    v = OptionSet.objects.order_by("name").values_list("name", flat=True)
    return [("", "")] + list(zip(v, v))


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


# DEFAULTS = {
#     "fieldset": {"css": "bg-red-200 p-2"},
#     # "css": {"question": "cursor-pointer",
#     #         "input": TailWindMixin.default_class,
#     #         "label": "block uppercase tracking-wide text-gray-700 font-bold mb-2"},
# }


# def get_initial(field, prefix):
#     base = DEFAULTS.get(prefix, {})
#     for k, v in field.advanced.get(prefix, {}).items():
#         if v:
#             base[k] = v
#     return base


#
# class FieldsetAttributesForm(AdvancendAttrsMixin, forms.Form):
#     title = "Fieldset"
#     css = forms.CharField(required=False, initial=TailWindMixin.default_class)


class FieldEditor:
    FORMS = {
        "field": FlexFieldAttributesForm,
        "smart": AdvancedForm,
        "custom": CustomForm,
        "config": ValidationForm,
        # "fieldset": FieldsetAttributesForm,
        # "kwargs": FormFieldAttributesForm,
        # "widget": WidgetAttributesForm,
        # "smart": SmartAttributesForm,
        "css": CssForm,
        "events": EventForm,
    }

    def __init__(self, modeladmin, request, pk):
        self.modeladmin = modeladmin
        self.request = request
        self.pk = pk
        self.cache_key = f"/editor/field/{self.request.user.pk}/{self.pk}/"

    @cached_property
    def field(self):
        return FlexFormField.objects.get(pk=self.pk)

    @cached_property
    def patched_field(self):
        fld = self.field
        fld.advanced = {}

        if config := cache.get(self.cache_key, None):
            merged = {}
            _forms: Dict[str, AdvancendAttrsForm] = self.get_forms(config)
            fieldForm = _forms.get("field", None)
            if fieldForm.is_valid():
                fld.field_type = field_registry.get_class(fieldForm.cleaned_data.pop("field_type"))
                for k, v in fieldForm.cleaned_data.items():
                    setattr(fld, k, v)
            else:
                raise ValidationError(fieldForm.errors)

            for __, frm in _forms.items():
                if frm.is_valid():
                    processed = []
                    for sect in AdvancendAttrsForm.SECTIONS_MAP.keys():
                        values = {k: v for k, v in frm.get_section(sect).items() if v and str(v).strip()}
                        processed.extend(values.keys())
                        if sect == "field":
                            for k, v in values.items():
                                setattr(fld, k, v)
                        else:
                            merged = merge_data(merged, {**{sect: values}})
                else:
                    raise ValidationError(frm.errors)
            fld.advanced = merged
        return fld

    def patch(self, request, pk):
        pass

    def get_kwargs(self):
        try:
            i = self.patched_field.get_instance()
            data = self.field.get_field_kwargs()
            data["field"]["widget"] = fqn(i.widget)

            # data["__field__"] = fqn(i)
            # data["__widget__"] = {"class": fqn(i.widget),
            #                       "attrs": i.widget.attrs}
            rendered = json.dumps(data, indent=4)
        except Exception as e:
            logger.exception(e)
            rendered = f"{e.__class__.__name__}: {e}"
        return HttpResponse(rendered, content_type="text/plain")

    def get_advanced(self):
        self.patched_field.get_instance()
        rendered = json.dumps(self.field.advanced, indent=4)
        return HttpResponse(rendered, content_type="text/plain")

    def get_html(self):
        from bs4 import BeautifulSoup as bs
        from bs4 import formatter
        from pygments import highlight
        from pygments.formatters.html import HtmlFormatter
        from pygments.lexers import HtmlLexer

        instance = self.patched_field.get_instance()
        form_class_attrs = {
            self.field.name: instance,
        }
        form_class = type(forms.Form)("TestForm", (forms.Form,), form_class_attrs)
        ctx = self.get_context(self.request)
        ctx["form"] = form_class()
        ctx["instance"] = instance
        code = Template(
            "{% for field in form %}{% spaceless %}"
            '{% include "smart/_fieldset.html" %}{% endspaceless %}{% endfor %}'
        ).render(Context(ctx))
        formatter = formatter.HTMLFormatter(indent=2)
        soup = bs(code)
        prettyHTML = soup.prettify(formatter=formatter)

        formatter = HtmlFormatter(style="default", full=True)
        ctx["code"] = highlight(prettyHTML, HtmlLexer(), formatter)
        return render(self.request, "admin/core/flexformfield/field_editor/code.html", ctx, content_type="text/html")

    def render(self):
        instance = self.patched_field.get_instance()
        form_class_attrs = {
            self.field.name: instance,
            "flex_form": Mock(),
        }
        form_class = type(FlexFormBaseForm)("TestForm", (FlexFormBaseForm,), form_class_attrs)
        ctx = self.get_context(self.request)
        if self.request.method == "POST":
            form = form_class(self.request.POST)
            ctx["valid"] = form.is_valid()
        else:
            form = form_class(initial={self.field.name: self.patched_field.get_default_value()})
            ctx["valid"] = None
        ctx["form"] = form
        ctx["media"] = VersionMedia() + form.media + instance.widget.media
        ctx["instance"] = instance

        return render(self.request, "admin/core/flexformfield/field_editor/preview.html", ctx)

    def get_forms(self, data=None) -> Dict:
        if data:
            return {prefix: Form(data, prefix=prefix, field=self.field) for prefix, Form in self.FORMS.items()}
        if self.request.method == "POST":
            return {
                prefix: Form(self.request.POST, prefix=prefix, field=self.field) for prefix, Form in self.FORMS.items()
            }
        return {prefix: Form(prefix=prefix, field=self.field) for prefix, Form in self.FORMS.items()}

    def refresh(self):
        forms = self.get_forms()
        if all(map(lambda f: f.is_valid(), forms.values())):
            data = self.request.POST.dict()
            data.pop("csrfmiddlewaretoken")
            cache.set(self.cache_key, data)
            return JsonResponse(data)
        else:
            return JsonResponse({prefix: frm.errors for prefix, frm in forms.items()}, status=400)

    def get_context(self, request, pk=None, **kwargs):
        return {
            **self.modeladmin.get_common_context(request, pk),
            **kwargs,
        }

    def get(self, request, pk):
        ctx = self.get_context(request, pk)
        ctx["forms"] = {}
        extra = "" if settings.DEBUG else ".min"
        media = VersionMedia()
        for prefix, frm in self.get_forms().items():
            # ctx[f"form_{prefix}"] = frm
            ctx["forms"][prefix] = frm
            media += frm.media

        media += VersionMedia(
            js=[
                "admin/js/vendor/jquery/jquery%s.js" % extra,
                "admin/js/jquery.init.js",
                "jquery.compat%s.js" % extra,
                "admin/resizer%s.js" % extra,
                "smart_validation%s.js" % extra,
                "smart%s.js" % extra,
                "smart_field%s.js" % extra,
            ],
            css={"all": ["admin/field_editor/field_editor.css"]},
        )
        ctx["media"] = media
        # + VersionMedia(js=["admin/field_editor/field_editor%s.js" % extra])
        return render(request, "admin/core/flexformfield/field_editor/main.html", ctx)

    def post(self, request, pk):
        forms = self.get_forms()
        if all(map(lambda f: f.is_valid(), forms.values())):
            self.patched_field.save()
            return HttpResponseRedirect(".")
        else:
            raise Exception("""---""")
