from django import forms
from django.forms import widgets


class HiddenField(forms.CharField):
    widget = widgets.HiddenInput

    def __init__(self, **kwargs):
        kwargs["required"] = False
        kwargs["label"] = ""
        kwargs["help_text"] = ""
        super().__init__(**kwargs)
