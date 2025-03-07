from django import forms
from django.utils.translation import gettext as _

from .mixins import MultiValueWidgetMixin
from .widgets import SmartTextWidget


class DocumentCountryInput(SmartTextWidget):
    def __init__(self, attrs=None):
        attrs = {
            "placeholder": _("Document country..."),
            **(attrs or {}),
        }
        super().__init__(attrs)


class DocumentNumberInput(SmartTextWidget):
    def __init__(self, attrs=None):
        attrs = {
            "placeholder": _("Document number..."),
            **(attrs or {}),
        }
        super().__init__(attrs)


class DocumentWidget(MultiValueWidgetMixin, forms.MultiWidget):
    def __init__(self, attrs=None):
        widgets = (DocumentCountryInput(attrs), DocumentNumberInput(attrs))
        super().__init__(widgets, attrs)

    def decompress(self, value):
        return value.split(",") if value else [None, None]


class DocumentField(forms.MultiValueField):
    widget = DocumentWidget

    def __init__(self, *args, **kwargs):
        fields = (
            forms.CharField(),
            forms.CharField(),
        )
        super().__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        return ",".join(data_list) if data_list else None
