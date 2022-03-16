import functools
import logging
from datetime import date, datetime, time

import jsonpickle
from admin_ordering.models import OrderableModel
from concurrency.fields import IntegerVersionField
from django import forms
from django.contrib.postgres.fields import CICharField
from django.core.cache import caches
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.template.defaultfilters import pluralize
from django_regex.fields import RegexField
from strategy_field.fields import StrategyClassField
from strategy_field.utils import fqn

from .fields import WIDGET_FOR_FORMFIELD_DEFAULTS, SmartFieldMixin
from .forms import FlexFormBaseForm, CustomFieldMixin
from .registry import field_registry, form_registry, import_custom_field
from .utils import jsonfy, namify, underscore_to_camelcase

logger = logging.getLogger(__name__)

cache = caches["default"]


class Validator(models.Model):
    FORM = "form"
    FIELD = "field"
    name = CICharField(max_length=255, unique=True)
    message = models.CharField(max_length=255)
    code = models.TextField(blank=True, null=True)
    target = models.CharField(max_length=5, choices=((FORM, "Form"), (FIELD, "Field")))

    def __str__(self):
        return self.name

    @staticmethod
    def js_type(value):
        if isinstance(value, (datetime, date, time)):
            return str(value)
        if isinstance(value, (dict,)):
            return jsonfy(value)
        return value

    def validate(self, value):
        from py_mini_racer import MiniRacer

        ctx = MiniRacer()
        ctx.eval(f"var value = {jsonpickle.encode(value)};")
        ret = ctx.eval(self.code)
        try:
            ret = jsonpickle.decode(ret)
        except TypeError:
            pass
        if not ret:
            raise ValidationError(self.message)


def get_validators(field):
    if field.validator:

        def inner(value):
            field.validator.validate(value)

        return [inner]
    return []


class FlexForm(models.Model):
    version = IntegerVersionField()
    name = CICharField(max_length=255, unique=True)
    base_type = StrategyClassField(registry=form_registry, default=FlexFormBaseForm)
    validator = models.ForeignKey(
        Validator, limit_choices_to={"target": Validator.FORM}, blank=True, null=True, on_delete=models.PROTECT
    )

    class Meta:
        verbose_name = "FlexForm"
        verbose_name_plural = "FlexForms"

    def __str__(self):
        return self.name

    def add_field(
        self,
        label,
        field_type=forms.CharField,
        required=False,
        choices=None,
        regex=None,
        validator=None,
        name=None,
        **kwargs,
    ):
        if isinstance(choices, (list, tuple)):
            kwargs["choices"] = choices
            choices = None
        return self.fields.update_or_create(
            label=label,
            defaults={
                "name": name,
                "field_type": field_type,
                "choices": choices,
                "regex": regex,
                "validator": validator,
                "advanced": kwargs,
                "required": required,
            },
        )[0]

    def add_formset(self, form, **extra):
        defaults = {"extra": 0, "name": form.name.lower() + pluralize(0)}
        defaults.update(extra)
        return FormSet.objects.update_or_create(parent=self, flex_form=form, defaults=defaults)[0]

    @functools.cache
    def get_form(self):
        fields = {}
        for field in self.fields.select_related("validator").order_by("ordering"):
            try:
                fields[field.name] = field.get_instance()
            except TypeError:
                pass
        form_class_attrs = {
            "flex_form": self,
            **fields,
        }
        flexForm = type(FlexFormBaseForm)(f"{self.name}FlexForm", (self.base_type,), form_class_attrs)
        return flexForm

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)
        self.get_form.cache_clear()


class FormSet(OrderableModel):
    version = IntegerVersionField()
    name = CICharField(max_length=255)
    parent = models.ForeignKey(FlexForm, on_delete=models.CASCADE, related_name="formsets")
    flex_form = models.ForeignKey(FlexForm, on_delete=models.CASCADE)
    extra = models.IntegerField(default=0, blank=False, null=False)
    max_num = models.IntegerField(default=None, blank=True, null=True)
    min_num = models.IntegerField(default=0, blank=False, null=False)

    dynamic = models.BooleanField(default=True)

    class Meta:
        verbose_name = "FormSet"
        verbose_name_plural = "FormSets"
        ordering = ["ordering"]
        unique_together = (("parent", "flex_form", "name"),)

    def __str__(self):
        return self.name

    def get_form(self):
        return self.flex_form.get_form()


class FlexFormField(OrderableModel):
    version = IntegerVersionField()
    flex_form = models.ForeignKey(FlexForm, on_delete=models.CASCADE, related_name="fields")
    label = models.CharField(max_length=2000)
    name = CICharField(max_length=30, blank=True)
    field_type = StrategyClassField(registry=field_registry, import_error=import_custom_field)
    choices = models.CharField(max_length=2000, blank=True, null=True)
    required = models.BooleanField(default=False)
    validator = models.ForeignKey(
        Validator, blank=True, null=True, limit_choices_to={"target": Validator.FIELD}, on_delete=models.PROTECT
    )
    regex = RegexField(blank=True, null=True)
    advanced = models.JSONField(default=dict, blank=True, null=True)

    class Meta:
        unique_together = (("flex_form", "name"),)
        verbose_name = "FlexForm Field"
        verbose_name_plural = "FlexForm Fields"
        ordering = ["ordering"]

    def __str__(self):
        return f"{self.name} {self.field_type}"

    def get_instance(self):
        # if hasattr(self.field_type, "custom") and isinstance(self.field_type.custom, CustomFieldType):
        if issubclass(self.field_type, CustomFieldMixin):
            field_type = self.field_type.custom.base_type
            kwargs = self.field_type.custom.attrs.copy()
            if self.validator:
                kwargs.setdefault("validators", get_validators(self))
            elif self.field_type.custom.validator:
                kwargs["validators"] = get_validators(self.field_type.custom)
            else:
                kwargs["validators"] = []
            kwargs.setdefault("label", self.label)
            kwargs.setdefault("required", self.required)
            regex = self.regex or self.field_type.custom.regex
        else:
            field_type = self.field_type
            kwargs = self.advanced.copy()
            regex = self.regex

            smart_attrs = kwargs.pop("smart", {})
            smart_attrs["data-flex"] = self.name
            kwargs.setdefault("smart_attrs", smart_attrs)

            kwargs.setdefault("label", self.label)
            kwargs.setdefault("required", self.required)
            kwargs.setdefault("validators", get_validators(self))
            # if self.choices and hasattr(field_type, "choices"):
            #     kwargs["choices"] = self.choices
        if field_type in WIDGET_FOR_FORMFIELD_DEFAULTS:
            kwargs = {**WIDGET_FOR_FORMFIELD_DEFAULTS[field_type], **kwargs}
        if "choices" not in kwargs and self.choices and hasattr(field_type, "choices"):
            kwargs["choices"] = clean_choices(self.choices.split(","))
        if regex:
            kwargs["validators"].append(RegexValidator(regex))
        try:
            tt = type(field_type.__name__, (SmartFieldMixin, field_type), dict())
            fld = tt(**kwargs)
        except Exception as e:
            logger.exception(e)
            raise
        return fld

    def clean(self):
        try:
            self.get_instance()
        except Exception as e:
            raise ValidationError(e)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.name:
            self.name = namify(self.label)
        else:
            self.name = namify(self.name)

        super().save(force_insert, force_update, using, update_fields)
        self.flex_form.get_form.cache_clear()


class OptionSet(models.Model):
    version = IntegerVersionField()
    name = CICharField(max_length=100, unique=True)
    description = models.CharField(max_length=1000, blank=True, null=True)
    data = models.TextField(blank=True, null=True)
    separator = models.CharField(max_length=1, default="", blank=True)
    columns = models.CharField(
        max_length=20, default="label", blank=True, help_text="column order. Es: 'pk,parent,label' or 'pk,label'"
    )

    def clean(self):
        cols = self.columns.split(",")
        if self.separator and len(cols) == 1:
            raise ValidationError("You must define columns order if 'separator' is set.")

        if len(cols) > 3:
            raise ValidationError("Invalid columns definition")

        super().clean()

    def get_cache_key(self):
        return f"options-{self.pk}-{self.name}-{self.version}"

    def get_data(self):
        value = cache.get(self.get_cache_key(), version=self.version)
        parent_col = None
        if not value:
            columns = self.columns.split(",")
            if len(columns) == 1:
                pk_col = label_col = 0
            if len(columns) > 1:
                pk_col = columns.index("pk")
            if len(columns) >= 2:
                label_col = columns.index("label")
            if len(columns) == 3 and "parent" in columns:
                parent_col = columns.index("parent")

            value = []
            for line in self.data.split("\r\n"):
                if not line.strip():
                    continue
                if len(columns) == 1:
                    pk, parent, label = line.strip().lower(), None, line
                else:
                    cols = line.split(self.separator)
                    if len(columns) == 3 and "parent" in columns:
                        pk, parent, label = cols[pk_col], cols[parent_col], cols[label_col]
                    elif len(columns) > 1:
                        pk, parent, label = cols[pk_col], None, cols[label_col]
                    else:
                        raise ValueError("")
                values = {
                    "pk": pk,
                    "parent": parent,
                    "label": label,
                }
                value.append(values)
            cache.set(self.get_cache_key(), value)
        return value

    def as_choices(self):
        data = self.get_data()
        for entry in data:
            yield entry["pk"], entry["label"]

    def as_json(self):
        return self.get_data()


def clean_choices(value):
    if not isinstance(value, (list, tuple)):
        raise ValueError("choices must be list or tuple")
    try:
        return list(dict(value).items())
    except ValueError:
        return list(zip(map(str.lower, value), value))


class CustomFieldType(models.Model):
    name = CICharField(max_length=100, unique=True, validators=[RegexValidator("[A-Z][a-zA-Z0-9_]*")])
    base_type = StrategyClassField(registry=field_registry, default=forms.CharField)
    attrs = models.JSONField(default=dict)
    regex = RegexField(blank=True, null=True)
    # choices = models.CharField(max_length=2000, blank=True, null=True)
    # required = models.BooleanField(default=False)
    validator = models.ForeignKey(
        Validator, blank=True, null=True, limit_choices_to={"target": Validator.FIELD}, on_delete=models.PROTECT
    )

    @staticmethod
    def build(name, defaults):
        choices = defaults.get("attrs", {}).get("choices", {})
        if choices:
            defaults["attrs"]["choices"] = clean_choices(choices)
        return CustomFieldType.objects.update_or_create(name=name, defaults=defaults)[0]

    def __str__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)
        cls = self.get_class()
        if fqn(cls) not in field_registry:
            field_registry.register(cls)

    def clean(self):
        try:
            kwargs = self.attrs.copy()
            class_ = self.get_class()
            class_(**kwargs)
        except Exception as e:
            raise ValidationError(f"Error instantiating {fqn(class_)}: {e}")

    def get_class(self):
        attrs = self.attrs.copy()
        attrs["custom"] = self
        return type(self.base_type)(underscore_to_camelcase(self.name), (CustomFieldMixin, self.base_type), attrs)
