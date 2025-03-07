from django import forms

from .mixins import TailWindMixin


class NumberWidget(TailWindMixin, forms.NumberInput):
    pass
