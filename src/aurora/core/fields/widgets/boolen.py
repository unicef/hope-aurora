from django import forms

from .mixins import TailWindMixin


class BooleanWidget(TailWindMixin, forms.CheckboxInput):
    template_name = "django/forms/widgets/boolean.html"
    default_class = ""
