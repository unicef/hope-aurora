from django import forms
from django.forms import HiddenInput

from aurora.state import state

from ..utils import get_client_ip
from .mixins import ConfigurableSmartField


class RemoteIpField(ConfigurableSmartField, forms.CharField):
    widget = HiddenInput

    def __init__(self, **kwargs):
        kwargs["required"] = False
        kwargs["label"] = ""
        kwargs["help_text"] = ""
        super().__init__(**kwargs)

    def to_python(self, value):
        return get_client_ip(state.request)
