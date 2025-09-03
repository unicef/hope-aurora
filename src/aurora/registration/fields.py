from django import forms
from django.contrib.postgres.fields import ArrayField
from django.forms import Field as FormField


class ChoiceArrayField(ArrayField):
    def formfield(self, **kwargs) -> FormField:
        defaults = {
            "form_class": forms.TypedMultipleChoiceField,
            "choices": self.base_field.choices,
            "coerce": self.base_field.to_python,
            "widget": forms.CheckboxSelectMultiple,
        }
        defaults.update(kwargs)
        return super(ArrayField, self).formfield(**defaults)
