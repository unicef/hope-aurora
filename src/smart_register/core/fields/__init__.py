from django import forms

from . import widgets
from .captcha import SmartCaptchaField
from .custom import CustomField
from .document import DocumentField
from .gis import LocationField
from .multi_checkbox import MultiCheckboxField
from .picture import PictureField
from .radio import RadioField, YesNoChoice, YesNoRadio
from .select import AjaxSelectField, SelectField
from .widgets.mixins import SmartFieldMixin
from .label import LabelOnlyField

WIDGET_FOR_FORMFIELD_DEFAULTS = {
    forms.DateField: {"widget": widgets.SmartDateWidget},
    forms.CharField: {"widget": widgets.SmartTextWidget},
    forms.IntegerField: {"widget": widgets.NumberWidget},
    forms.FloatField: {"widget": widgets.NumberWidget},
    forms.ChoiceField: {"widget": widgets.SmartChoiceWidget},
    RadioField: {"widget": widgets.RadioWidget},
    YesNoRadio: {"widget": widgets.YesNoRadioWidget},
    YesNoChoice: {"widget": widgets.SmartSelectWidget},
    MultiCheckboxField: {"widget": widgets.MultiCheckboxWidget},
}
