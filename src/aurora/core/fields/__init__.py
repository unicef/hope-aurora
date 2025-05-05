from django import forms
from django.forms.fields import CharField, DateField

from . import widgets
from .captcha import CaptchaField
from .compilation_time import CompilationTimeField
from .document import DocumentField
from .file import SmartFileField
from .gis import LocationField
from .hidden import HiddenField
from .label import LabelOnlyField
from .mixins import SmartFormField
from .multi_checkbox import MultiCheckboxField
from .radio import RadioField, YesNoChoice, YesNoRadio
from .remote_ip import RemoteIpField
from .select import AjaxSelectField, SelectField, SmartSelectWidget
from .uba import UBANameEnquiryField
from .webcam import WebcamField
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

WIDGET_FOR_FORMFIELD_DEFAULTS = {
    DateField: {"widget": widgets.SmartDateWidget},
    CharField: {
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

__all__ = ["CharField", "DateField", "CompilationTimeField", "SmartFileField"]
