import json

from typing import Dict

from django import forms
from django.core.cache import caches
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.functional import cached_property

from aurora.core.models import FlexFormField
from aurora.core.utils import merge_data

cache = caches["default"]


class AdvancendAttrsMixin:
    def __init__(self, *args, **kwargs):
        self.field = kwargs.pop("field", None)
        self.prefix = kwargs.get("prefix")
        if self.field:
            kwargs["initial"] = self.field.advanced.get(self.prefix, {})
        super().__init__(*args, **kwargs)


class FlexFieldAttributesForm(AdvancendAttrsMixin, forms.ModelForm):
    required = forms.BooleanField(widget=forms.CheckboxInput, required=False)

    class Meta:
        model = FlexFormField
        fields = ("field_type", "label", "name", "choices", "required", "validator", "regex")


class FormFieldAttributesForm(AdvancendAttrsMixin, forms.Form):
    default_value = forms.CharField(required=False, help_text="default value for the field")


class WidgetAttributesForm(AdvancendAttrsMixin, forms.Form):
    placeholder = forms.CharField(required=False, help_text="placeholder for the input")
    class_ = forms.CharField(label="Field class", required=False, help_text="Input CSS class to apply (will")
    extra_classes = forms.CharField(required=False, help_text="Input CSS classes to add input")
    fieldset = forms.CharField(label="Fieldset class", required=False, help_text="Fieldset CSS class to apply")
    onchange = forms.CharField(required=False, help_text="Javascfipt onchange event")


class SmartAttributesForm(AdvancendAttrsMixin, forms.Form):
    question = forms.CharField(required=False, help_text="If set, user must check related box to display the field")
    hint = forms.CharField(required=False, help_text="Text to display above the input")
    description = forms.CharField(required=False, help_text="Text to display below the input")
    datasource = forms.CharField(required=False, help_text="Datasource name for ajax field")


class FieldEditor:
    FORMS = {
        "field": FlexFieldAttributesForm,
        "kwargs": FormFieldAttributesForm,
        "widget_kwargs": WidgetAttributesForm,
        "smart": SmartAttributesForm,
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
        if config := cache.get(self.cache_key, None):
            forms = self.get_forms(config)
            fieldForm = forms.pop("field", None)
            if fieldForm.is_valid():
                for k, v in fieldForm.cleaned_data.items():
                    setattr(fld, k, v)
            for prefix, frm in forms.items():
                frm.is_valid()
                merged = merge_data(fld.advanced, {**{prefix: frm.cleaned_data}})
                fld.advanced = merged
        return fld
        # formField = FlexFieldAttributesForm(config, prefix="field")
        # formAttrs = FormFieldAttributesForm(config, prefix="kwargs")
        # formWidget = WidgetAttributesForm(config, prefix="widget_kwargs")
        # formSmart = SmartAttributesForm(config, prefix="smart")
        # if all(map(lambda x: x.is_valid(), [formSmart, formWidget, formAttrs, formField])):
        #     base.required = parse_bool(config.get("field", {}).pop("required", False))
        #     for k, v in config.get("field", {}).items():
        #         setattr(base, k, v)
        #     if field_type := config.get("field", {}).pop("field_type", None):
        #         base.field_type = field_type
        #     #     base.field_type = field_type
        #     config = merge_data(base.advanced, {**formWidget.cleaned_data})
        #     base.advanced = config
        # else:
        #     raise ValidationError(formField.errors)
        # instance = base.get_instance()
        # return instance

    def patch(self, request, pk):
        pass

    def get_configuration(self):
        self.patched_field.get_instance()
        rendered = json.dumps(self.field.advanced, indent=4)
        return HttpResponse(rendered, content_type="text/plain")

    def get_code(self):
        instance = self.patched_field.get_instance()
        form_class_attrs = {
            "sample": instance,
        }
        form_class = type(forms.Form)("TestForm", (forms.Form,), form_class_attrs)
        ctx = self.modeladmin.get_common_context(self.request)
        ctx["form"] = form_class()
        ctx["instance"] = instance
        return render(self.request, "admin/core/flexformfield/field_editor/code.html", ctx, content_type="text/plain")

    def render(self):
        instance = self.patched_field.get_instance()
        form_class_attrs = {
            "sample": instance,
        }
        form_class = type(forms.Form)("TestForm", (forms.Form,), form_class_attrs)
        ctx = self.modeladmin.get_common_context(self.request)
        if self.request.method == "POST":
            form = form_class(self.request.POST)
            ctx["valid"] = form.is_valid()
        else:
            form = form_class()
            ctx["valid"] = None

        ctx["form"] = form
        ctx["instance"] = instance

        return render(self.request, "admin/core/flexformfield/field_editor/preview.html", ctx)

    def get_forms(self, data=None) -> Dict:
        if data:
            return {prefix: Form(data, prefix=prefix, field=self.field) for prefix, Form in self.FORMS.items()}
        elif self.request.method == "POST":
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
        else:
            return JsonResponse({frm.prefix: frm.errors for frm in forms}, status=400)
        return JsonResponse(data)

    def get(self, request, pk):
        ctx = self.modeladmin.get_common_context(request, pk)
        # i = {"field_type": fqn(obj.field_type)}
        # i.update(**obj.advanced.get("kwargs", {}))
        formField = FlexFieldAttributesForm(prefix="field", instance=self.field, field=self.field)
        formAttrs = FormFieldAttributesForm(prefix="kwargs", field=self.field)
        formWidget = WidgetAttributesForm(prefix="widget_kwargs", field=self.field)
        formSmart = SmartAttributesForm(prefix="smart", field=self.field)

        ctx["form_field"] = formField
        ctx["form_attrs"] = formAttrs
        ctx["form_widget"] = formWidget
        ctx["form_smart"] = formSmart
        return render(request, "admin/core/flexformfield/field_editor/main.html", ctx)

    def post(self, request, pk):
        pass
