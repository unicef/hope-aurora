import logging
import re

import jmespath
from adminfilters.querystring import QueryStringFilter
from django import forms
from django.core.exceptions import ValidationError
from django_regex.utils import RegexList
from mdeditor.fields import MDTextFormField

from aurora.registration.models import Record

from .models import Registration

logger = logging.getLogger(__name__)


class JMESPathFormField(forms.CharField):
    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        attrs.setdefault("style", "width:80%")
        return attrs

    def validate(self, value):
        super().validate(value)
        if value not in self.empty_values:
            try:
                jmespath.compile(value)
            except Exception as e:
                raise ValidationError(str(e)) from None


def as_link(param):
    return f'<a target="_new" href="{param}">{param}</a>'


class RegistrationForm(forms.ModelForm):
    unique_field_path = JMESPathFormField(
        required=False,
        help_text=f"JAMESPath expression. Read more at {as_link('https://jmespath.org/')}",
    )
    intro = MDTextFormField(required=False)
    footer = MDTextFormField(required=False)

    class Meta:
        model = Registration
        fields = (
            "version",
            "name",
            "title",
            "slug",
            "project",
            "flex_form",
            "start",
            "end",
            "active",
            "archived",
            "locale",
            "dry_run",
            "handler",
            "show_in_homepage",
            "welcome_page",
            "locales",
            "intro",
            "footer",
            "client_validation",
            "validator",
            "scripts",
            "unique_field_path",
            "unique_field_error",
            "public_key",
            "encrypt_data",
            "advanced",
            "protected",
            "is_pwa_enabled",
            "export_allowed",
        )


class CloneForm(forms.Form):
    title = forms.CharField(label="New Name")
    deep = forms.BooleanField(
        required=False,
        help_text="Clone all forms and fields too. "
        "This will create a fully independent registration, form and components",
    )


class RegistrationOptionForm(forms.ModelForm):
    datatable = forms.BooleanField(required=False, help_text="enable datatable inspection for this data")
    export = forms.BooleanField(required=False, help_text="allows data to be exported in CSV")


class RegistrationExportForm(forms.Form):
    defaults = {}
    filters = forms.CharField(
        widget=forms.Textarea({"rows": 3, "cols": 80}),
        required=False,
        help_text="filters to use to select the records (Uses Django filtering syntax)",
    )
    include = forms.CharField(
        widget=forms.Textarea({"rows": 3, "cols": 80}),
        required=False,
        help_text="list the fields should be added. Regex can be used in each line.",
    )
    exclude = forms.CharField(
        widget=forms.Textarea({"rows": 3, "cols": 80}),
        required=False,
        help_text="list the fields should be ignored. Regex can be used in each line.",
    )

    def clean_filters(self):
        qs_filter = QueryStringFilter(None, {}, Record, None)
        return qs_filter.get_filters(self.cleaned_data["filters"])

    def clean_include(self):
        try:
            patterns = [p for p in self.cleaned_data.get("include", ".*").split("\n") if p.strip()]
            return RegexList([re.compile(rule) for rule in patterns] or [".*"])
        except Exception as e:
            raise ValidationError(e) from e

    def clean_exclude(self):
        try:
            return RegexList([re.compile(rule) for rule in self.cleaned_data["exclude"].split("\n")])
        except Exception as e:
            raise ValidationError(e) from None


class JamesForm(forms.ModelForm):
    unique_field_path = forms.CharField(
        label="JMESPath expression",
        widget=forms.TextInput(attrs={"style": "width:90%"}),
    )
    data = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = Registration
        fields = ("unique_field_path", "data")

    class Media:
        js = [
            "https://cdnjs.cloudflare.com/ajax/libs/jmespath/0.16.0/jmespath.min.js",
        ]


class DecryptForm(forms.Form):
    key = forms.CharField(widget=forms.Textarea)
