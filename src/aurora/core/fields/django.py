from typing import Any

from django import forms
from django.core.exceptions import ValidationError

from .mixins import ConfigurableSmartField
from .widgets import SmartDateWidget, SmartTextWidget, ImageWidget


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
    widget = ImageWidget

    def __init__(self, *, max_length=None, allow_empty_file=False, **kwargs):
        self.max_size = kwargs.pop("max_size", None)
        super().__init__(max_length=max_length, allow_empty_file=allow_empty_file, **kwargs)

    def clean(self, data: Any, initial: Any | None = None) -> Any:
        image = super().clean(data, initial)
        if self.max_size is not None and image.size > self.max_size:
            raise ValidationError("Image too big.")
        return image


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
