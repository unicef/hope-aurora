from django import forms

from .mixins import ConfigurableSmartField
from .widgets.mixins import TailWindMixin


class LabelOnlyWidget(TailWindMixin, forms.TextInput):
    template_name = "django/forms/widgets/label.html"


class LabelOnlyField(ConfigurableSmartField, forms.CharField):
    widget = LabelOnlyWidget
    storage = None
