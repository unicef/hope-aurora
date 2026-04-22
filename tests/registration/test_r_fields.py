from django import forms
from django.db import models

from aurora.registration.fields import ChoiceArrayField


def test_choice_array_field_formfield_defaults():
    field = ChoiceArrayField(
        models.IntegerField(choices=[(1, "One"), (2, "Two")]),
        default=list,
    )

    form_field = field.formfield()

    assert isinstance(form_field, forms.TypedMultipleChoiceField)
    assert form_field.choices == [(1, "One"), (2, "Two")]
    assert form_field.coerce("1") == 1
    assert isinstance(form_field.widget, forms.CheckboxSelectMultiple)


def test_choice_array_field_formfield_accepts_overrides():
    field = ChoiceArrayField(
        models.CharField(max_length=20, choices=[("a", "A"), ("b", "B")]),
        default=list,
    )

    form_field = field.formfield(required=False, choices=[("x", "X")], coerce=str.upper)

    assert form_field.required is False
    assert form_field.choices == [("x", "X")]
    assert form_field.coerce("foo") == "FOO"
