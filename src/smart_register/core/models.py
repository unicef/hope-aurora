import json
import logging

from django import forms
from django.contrib.postgres.fields import CICharField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from strategy_field.fields import StrategyClassField

from .registry import registry

logger = logging.getLogger(__name__)


class Validator(models.Model):
    name = CICharField(max_length=255, unique=True)
    message = models.CharField(max_length=255)
    code = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    def validate(self, value):
        try:
            import pyduktape
            context = pyduktape.DuktapeContext()
            context.set_globals(value=value)
            res = json.dumps(context.eval_js(self.code))
            if not res:
                raise ValidationError(self.message)
        except Exception as e:
            logger.exception(e)
            raise Exception()


def get_validators(field):
    if field.validator:
        def inner(value):
            field.validator.validate(value)

        return [inner]
    return []


class FlexForm(models.Model):
    name = CICharField(max_length=255, unique=True)
    validation = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    def get_form(self):
        fields = {}
        for field in self.fields.all():
            fields[field.name] = field.field(label=field.label,
                                             required=field.required,
                                             validators=get_validators(field),
                                             )
        form_class_attrs = {
            **fields,
        }
        flexForm = type(forms.Form)(self.name, (forms.Form,), form_class_attrs)
        return flexForm


class ChildForm(models.Model):
    name = CICharField(max_length=255, unique=True)
    parent = models.ForeignKey(FlexForm, on_delete=models.CASCADE, related_name="childs")
    flex_form = models.ForeignKey(FlexForm, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_form(self):
        return self.flex_form.get_form()


class FlexFormField(models.Model):
    flex_form = models.ForeignKey(FlexForm, on_delete=models.CASCADE, related_name='fields')
    label = models.CharField(max_length=30)
    name = models.CharField(max_length=30, blank=True)
    field = StrategyClassField(registry=registry)
    required = models.BooleanField(default=False)
    validator = models.ForeignKey(Validator, blank=True, null=True, on_delete=models.PROTECT)

    class Meta:
        unique_together = ('name', 'flex_form'),

    def __str__(self):
        return f"{self.name} {self.field}"

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.name:
            self.name = slugify(self.label)

        super().save(force_insert, force_update, using, update_fields)
