from django import forms

from .mixins import TailWindMixin


class SmartTextWidget(TailWindMixin, forms.TextInput):
    def __init__(self, attrs=None):
        super().__init__(attrs=attrs)
