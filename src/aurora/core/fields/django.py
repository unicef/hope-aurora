from django import forms

from .mixins import ConfigurableSmartField
from .widgets import SmartDateWidget, SmartTextWidget


class BooleanField(ConfigurableSmartField, forms.BooleanField):
    pass


class CharField(ConfigurableSmartField, forms.CharField):
    widget = SmartTextWidget


class ChoiceField(ConfigurableSmartField, forms.ChoiceField):
    pass


class DateField(ConfigurableSmartField, forms.DateField):
    widget = SmartDateWidget


class DateTimeField(ConfigurableSmartField, forms.DateTimeField):
    pass


class DurationField(ConfigurableSmartField, forms.DurationField):
    pass


class EmailField(ConfigurableSmartField, forms.EmailField):
    pass


class FloatField(ConfigurableSmartField, forms.FloatField):
    pass


class GenericIPAddressField(ConfigurableSmartField, forms.GenericIPAddressField):
    pass


class ImageField(ConfigurableSmartField, forms.ImageField):
    pass


class IntegerField(ConfigurableSmartField, forms.IntegerField):
    pass


class MultipleChoiceField(ConfigurableSmartField, forms.MultipleChoiceField):
    pass


class NullBooleanField(ConfigurableSmartField, forms.NullBooleanField):
    pass


class TimeField(ConfigurableSmartField, forms.TimeField):
    pass


class URLField(ConfigurableSmartField, forms.URLField):
    pass
