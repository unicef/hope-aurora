import logging

from django import forms
from django.forms import BoundField
from django.urls import NoReverseMatch, reverse
from django.utils.translation import get_language

from .widgets.selected import AjaxSelectWidget, SmartSelectWidget

logger = logging.getLogger(__name__)


class SelectField(forms.ChoiceField):
    widget = SmartSelectWidget

    def __init__(self, **kwargs):
        self._choices = ()
        self.language = kwargs.pop("language", get_language())
        self.parent = kwargs.pop("parent_datasource", None)
        options = kwargs.pop("datasource", "")
        super().__init__(**kwargs)
        self.choices = options

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        if self.parent:
            attrs["data-parent"] = self.parent
        return attrs

    def _get_options(self):
        return self._options

    def _set_options(self, value):
        if value:  # pragma: no branch
            try:
                from aurora.core.models import OptionSet

                optset = OptionSet.objects.get_from_cache(value)
                value = list(optset.as_choices(self.language))
            except OptionSet.DoesNotExist as e:
                logger.exception(e)
                value = []
        self._options = self.widget.choices = value

    choices = property(_get_options, _set_options)


class AjaxSelectField(forms.Field):
    widget = AjaxSelectWidget

    def __init__(self, **kwargs):
        if hasattr(self, "smart_attrs"):
            self.parent = self.smart_attrs.get("parent_datasource", None)
            self.datasource = self.smart_attrs.get("datasource", None)
        elif "datasource" in kwargs:
            self.datasource = kwargs["datasource"]
        else:
            self.datasource = None
            self.parent = None

        super().__init__(**kwargs)

    def widget_attrs(self, widget):
        from aurora.core.models import OptionSet

        attrs = super().widget_attrs(widget)
        try:
            if self.parent:
                attrs["data-parent"] = self.parent
            attrs["data-source"] = self.datasource
            attrs["data-ajax--url"] = reverse("optionset", args=[self.datasource])
        except (OptionSet.DoesNotExist, NoReverseMatch, TypeError) as e:
            logger.exception(e)

        return attrs

    def get_bound_field(self, form, field_name):
        ret = BoundField(form, self, field_name)
        ret.field.widget.attrs["data-name"] = ret.name
        ret.field.widget.attrs["data-label"] = ret.label
        return ret
