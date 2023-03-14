from django import forms

from . import widgets
from .compilation_time import CompilationTimeField
from .document import DocumentField
from .file import SmartFileField
from .gis import LocationField
from .hidden import HiddenField
from .label import LabelOnlyField
from .mixins import SmartFieldMixin
from .multi_checkbox import MultiCheckboxField
from .radio import RadioField, YesNoChoice, YesNoRadio
from .remote_ip import RemoteIpField
from .select import AjaxSelectField, SelectField, SmartSelectWidget
from .webcam import WebcamField

WIDGET_FOR_FORMFIELD_DEFAULTS = {
    forms.DateField: {"widget": widgets.SmartDateWidget},
    forms.CharField: {"widget": widgets.SmartTextWidget, "max_length": 200, "strip": True},
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
