from django import forms
from django.forms import widgets

from .mixins import ConfigurableSmartField


class HiddenField(ConfigurableSmartField, forms.CharField):
    widget = widgets.HiddenInput

    def __init__(self, **kwargs):
        kwargs["required"] = False
        kwargs["label"] = ""
        kwargs["help_text"] = ""
        super().__init__(**kwargs)
