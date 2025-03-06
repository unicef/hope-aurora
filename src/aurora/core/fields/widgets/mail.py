from django import forms

from .mixins import TailWindMixin


class EmailWidget(TailWindMixin, forms.EmailInput):
    def __init__(self, attrs=None):
        super().__init__(attrs=attrs)
