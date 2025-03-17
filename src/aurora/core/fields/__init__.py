from django import forms

from . import widgets  # noqa
from .captcha import CaptchaField  # noqa
from .compilation_time import CompilationTimeField  # noqa
from .document import DocumentField  # noqa
from .file import SmartFileField  # noqa
from .gis import LocationField  # noqa
from .hidden import HiddenField  # noqa
from .label import LabelOnlyField  # noqa
from .mixins import SmartFieldMixin  # noqa
from .multi_checkbox import MultiCheckboxField  # noqa
from .radio import RadioField, YesNoChoice, YesNoRadio  # noqa
from .remote_ip import RemoteIpField  # noqa
from .selected import AjaxSelectField, SelectField, SmartSelectWidget  # noqa
from .uba import UBANameEnquiryField  # noqa
from .webcam import WebcamField  # noqa

WIDGET_FOR_FORMFIELD_DEFAULTS = {
    forms.DateField: {"widget": widgets.SmartDateWidget},
    forms.CharField: {
        "widget": widgets.SmartTextWidget,
        "max_length": 200,
        "strip": True,
    },
    forms.BooleanField: {"widget": widgets.BooleanWidget},
    forms.EmailField: {"widget": widgets.EmailWidget},
    forms.IntegerField: {"widget": widgets.NumberWidget},
    forms.FloatField: {"widget": widgets.NumberWidget},
    forms.ChoiceField: {"widget": SmartSelectWidget},
    forms.ImageField: {"widget": widgets.ImageWidget},
    # forms.FileField: {"widget": widgets.UploadFileWidget},
    SelectField: {"widget": SmartSelectWidget},
    RadioField: {"widget": widgets.RadioWidget},
    YesNoRadio: {"widget": widgets.YesNoRadioWidget},
    YesNoChoice: {"widget": SmartSelectWidget},
    # MultiCheckboxField: {"widget": widgets.MultiCheckboxWidget},
}
