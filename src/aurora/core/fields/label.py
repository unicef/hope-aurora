from django import forms

from .widgets.mixins import TailWindMixin
from .mixins import ConfigurableSmartField


class LabelOnlyWidget(TailWindMixin, forms.TextInput):
    template_name = "django/forms/widgets/label.html"


class LabelOnlyField(ConfigurableSmartField, forms.CharField):
    widget = LabelOnlyWidget
    storage = None
