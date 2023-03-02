from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms import BaseFormSet
from django.templatetags.static import static

from .fields.widgets import PythonEditor


class ValidatorForm(forms.ModelForm):
    code = forms.CharField(widget=PythonEditor)


class Select2Widget(forms.Select):
    template_name = "django/forms/widgets/select2.html"


class CustomFieldMixin:
    custom = None


class FlexFormBaseForm(forms.Form):
    flex_form = None
    compilation_time_field = None
    indexes = {"1": None, "2": None, "3": None}

    def get_counters(self, data):
        if self.compilation_time_field:
            return data.pop(self.compilation_time_field, {})
        return {}

    def is_valid(self):
        return super().is_valid()

    @property
    def media(self):
        extra = "" if settings.DEBUG else ".min"
        base = super().media
        return base + forms.Media(
            js=[
                static("smart_validation%s.js" % extra),
                static("smart%s.js" % extra),
            ]
        )

    def get_storage_mapping(self):
        return {name: field.storage for name, field in self.fields.items()}

    def _clean_fields(self):
        super()._clean_fields()
        for name, field in self.fields.items():
            if not field.is_stored():
                del self.cleaned_data[name]

    def full_clean(self):
        return super().full_clean()

    def clean(self):
        cleaned_data = self.cleaned_data
        # if self.is_valid() and self.flex_form and self.flex_form.validator:
        if self.flex_form.validator:
            try:
                self.flex_form.validator.validate(cleaned_data)
            except ValidationError as e:
                raise ValidationError(e)
        return cleaned_data


class SmartBaseFormSet(BaseFormSet):
    def non_form_errors(self):
        return super().non_form_errors()

    def clean(self):
        if self.fs.validator:
            data = {
                "total_form_count": self.total_form_count(),
                "errors": self._errors,
                "non_form_errors": self._non_form_errors,
                "cleaned_data": getattr(self, "cleaned_data", []),
            }
            try:
                self.fs.validator.validate(data)
            except ValidationError as e:
                raise ValidationError([e])

    @property
    def media(self):
        extra = "" if settings.DEBUG else ".min"
        base = super().media
        return base + forms.Media(
            js=[
                static("jquery.formset%s.js" % extra),
                static("smart.formset%s.js" % extra),
            ]
        )


class FieldAttributesForm(forms.Form):
    default_value = forms.CharField(required=False, help_text="default value for the field")
    choices = forms.JSONField(required=False)
    visible = forms.BooleanField(required=False)
    required = forms.BooleanField(required=False)


class WidgetAttributesForm(forms.Form):
    placeholder = forms.CharField(required=False, help_text="placeholder for the input")
    class_ = forms.CharField(label="Field class", required=False, help_text="Input CSS class to apply (will")
    extra_classes = forms.CharField(required=False, help_text="Input CSS classes to add input")
    fieldset = forms.CharField(label="Fieldset class", required=False, help_text="Fieldset CSS class to apply")
    onchange = forms.CharField(required=False, help_text="Javascfipt onchange event")


class SmartAttributesForm(forms.Form):
    question = forms.CharField(required=False, help_text="If set, user must check related box to display the field")
    hint = forms.CharField(required=False, help_text="Text to display above the input")
    description = forms.CharField(required=False, help_text="Text to display below the input")
    datasource = forms.CharField(required=False, help_text="Datasource name for ajax field")
