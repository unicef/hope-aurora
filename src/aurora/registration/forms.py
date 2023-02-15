import jmespath
from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from mdeditor.fields import MDTextFormField

from aurora.registration.models import Registration


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
                raise ValidationError(str(e))


def as_link(param):
    return mark_safe(f'<a target="_new" href="{param}">{param}</a>')


class RegistrationForm(forms.ModelForm):
    unique_field_path = JMESPathFormField(
        required=False, help_text=mark_safe("JAMESPath expression. " f"Read more at {as_link('https://jmespath.org/')}")
    )
    intro = MDTextFormField(required=False)
    footer = MDTextFormField(required=False)

    class Meta:
        model = Registration
        exclude = ()


class CloneForm(forms.Form):
    title = forms.CharField(label="New Name")
    deep = forms.BooleanField(
        required=False,
        help_text="Clone all forms and fields too. "
        "This will create a fully independent registration, form and components",
    )


class RegistrationOTPForm(forms.Form):
    emails = forms.CharField(widget=forms.Textarea, required=True)
    validity = forms.IntegerField(default=1, help_text="Number of days the invitation will be valid.")
