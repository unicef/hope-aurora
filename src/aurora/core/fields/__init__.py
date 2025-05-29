from typing import Any

from django import forms
from django.forms.fields import CharField, DateField

from . import widgets
from .captcha import CaptchaField
from .compilation_time import CompilationTimeField
from .django import (
    BooleanField,
    CharField,
    ChoiceField,
    DateField,
    DateTimeField,
    DurationField,
    EmailField,
    FloatField,
    GenericIPAddressField,
    ImageField,
    IntegerField,
    MultipleChoiceField,
    NullBooleanField,
    TimeField,
    URLField,
)
from .document import DocumentField
from .file import SmartFileField
from .gis import LocationField
from .hidden import HiddenField
from .label import LabelOnlyField
from .mixins import ConfigurableSmartField, SmartFormField
from .multi_checkbox import MultiCheckboxField
from .radio import RadioField, YesNoChoice, YesNoRadio
from .remote_ip import RemoteIpField
from .select import AjaxSelectField, SelectField, SmartSelectWidget
from .uba import UBANameEnquiryField
from .webcam import WebcamField

WIDGET_FOR_FORMFIELD_DEFAULTS: dict[type[ConfigurableSmartField], dict[str, Any]] = {
    # weird issues from mypy. does not recognize it as ConfigurableSmartField
    CharField: {  # type: ignore [dict-item]
        "widget": widgets.SmartTextWidget,
        "max_length": 200,
        "strip": True,
    },
    BooleanField: {"widget": widgets.BooleanWidget},
    EmailField: {"widget": widgets.EmailWidget},
    IntegerField: {"widget": widgets.NumberWidget},
    FloatField: {"widget": widgets.NumberWidget},
    ChoiceField: {"widget": SmartSelectWidget},
    ImageField: {"widget": widgets.ImageWidget},
    # forms.FileField: {"widget": widgets.UploadFileWidget},
    SelectField: {"widget": SmartSelectWidget},
    RadioField: {"widget": widgets.RadioWidget},
    YesNoRadio: {"widget": widgets.YesNoRadioWidget},
    YesNoChoice: {"widget": SmartSelectWidget},
    # MultiCheckboxField: {"widget": widgets.MultiCheckboxWidget},
}

__all__ = [
    "CharField",
    "CompilationTimeField",
    "DateField",
    "IntegerField",
    "SmartFileField",
    "SmartFormField",
    "WIDGET_FOR_FORMFIELD_DEFAULTS",
]
