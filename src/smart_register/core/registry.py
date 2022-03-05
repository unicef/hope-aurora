from django import forms
from strategy_field.registry import Registry
from . import widgets

WIDGET_FOR_FORMFIELD_DEFAULTS = {
    forms.DateField: {'widget': widgets.SmartDateWidget}
}


class FieldRegistry(Registry):
    pass


registry = FieldRegistry(forms.Field)

registry.register(forms.BooleanField)
registry.register(forms.CharField)
registry.register(forms.ChoiceField)
registry.register(forms.DateField)
registry.register(forms.DateTimeField)
registry.register(forms.DurationField)
registry.register(forms.EmailField)
registry.register(forms.FloatField)
registry.register(forms.GenericIPAddressField)
registry.register(forms.IntegerField)
registry.register(forms.MultipleChoiceField)
registry.register(forms.NullBooleanField)
registry.register(forms.TimeField)
registry.register(forms.URLField)
