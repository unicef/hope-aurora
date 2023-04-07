from django import forms

from aurora.core import fields


class BooleanFieldExtra(forms.Form):
    captions = forms.CharField(required=False)
    position = forms.ChoiceField(choices=(["l", "Left"], ["r", "right"]))


fields_config = {fields.BooleanField: BooleanFieldExtra}
