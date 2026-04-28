import contextlib
from unittest import mock
from unittest.mock import Mock

import pytest
from django import forms
from pytest_django import DjangoAssertNumQueries

from aurora.core.cache import Cache, cache_form, cache_formset
from aurora.core.fields import CompilationTimeField
from aurora.core.models import FlexForm
from aurora.state import state


@pytest.fixture
def simple_form(db) -> FlexForm:
    from aurora.core.cache import cache
    from aurora.core.models import Validator

    cache.clear()

    v1, __ = Validator.objects.update_or_create(
        label="length_1_50",
        defaults={
            "active": True,
            "target": Validator.FIELD,
            "code": "value.length>1 && value.length<=50 ? true: 'String size 1 to 5'",
        },
    )
    v2, __ = Validator.objects.update_or_create(
        label="length_2_10",
        defaults={
            "active": True,
            "target": Validator.FIELD,
            "code": "value.length>2 && value.length<=10 ? true: 'String size 2 to 10';",
        },
    )
    from testutils.factories import FormFactory

    frm = FormFactory(name="Form1")
    frm.fields.get_or_create(label="time", enabled=True, defaults={"field_type": CompilationTimeField})
    frm.fields.get_or_create(
        label="First Name", enabled=True, defaults={"field_type": forms.CharField, "required": True}
    )
    frm.fields.get_or_create(
        label="Last Name",
        enabled=True,
        defaults={
            "field_type": forms.CharField,
            "required": True,
            "validator": v2,
            "advanced": {"smart": {"index": 1}},
        },
    )
    frm.fields.get_or_create(label="Image", enabled=True, defaults={"field_type": forms.ImageField, "required": False})
    frm.fields.get_or_create(label="File", enabled=True, defaults={"field_type": forms.FileField, "required": False})
    frm.fields.get_or_create(
        label="index_no", enabled=True, defaults={"field_type": forms.CharField, "required": False}
    )
    return frm


@contextlib.contextmanager
def set_state():
    state.request = Mock(LANGUAGE_CODE="en-us")
    yield
    state.request = None


def test_cache_form(simple_form, django_assert_num_queries: DjangoAssertNumQueries) -> None:
    from aurora.core.cache import cache

    get_form_class = FlexForm.get_form_class
    get_formsets_classes = FlexForm.get_formsets_classes
    cache.clear()
    with mock.patch("aurora.core.models.FlexForm.get_form_class", cache_form(get_form_class)):
        with mock.patch("aurora.core.models.FlexForm.get_formsets_classes", cache_formset(get_formsets_classes)):
            frm = FlexForm.objects.get(pk=simple_form.pk)

            with set_state():
                form = frm.get_form_class()()
                formsets = frm.get_formsets({})
                assert str(form)
                assert str(formsets)
                with django_assert_num_queries(0):
                    form = frm.get_form_class()()
                    formsets = frm.get_formsets({})
                    assert str(form)
                    assert str(formsets)


def test_cache():
    c = Cache()
    c["one"] = 1
    assert len(c) == 1
    c["two"] = 1
    assert len(c) == 2

    c = Cache(size=1)
    c["one"] = 1
    assert len(c) == 1
    c["two"] = 1
    assert len(c) == 1

    c.clear()
    assert len(c) == 0


def test_cache_size_limit():
    test_cache = Cache(size=2)
    test_cache["key1"] = "value1"
    test_cache["key2"] = "value2"
    test_cache["key3"] = "value3"

    assert len(test_cache) == 2
    assert "key1" not in test_cache
    assert "key2" in test_cache
    assert "key3" in test_cache


def test_cache_clear():
    test_cache = Cache(size=10)
    test_cache["key1"] = "value1"
    test_cache["key2"] = "value2"
    test_cache.clear()
    assert len(test_cache) == 0


def test_cache_form_hit():
    mock_request = Mock()
    mock_request.LANGUAGE_CODE = "en-us"
    state.request = mock_request

    mock_form = Mock()
    mock_form.pk = 1
    mock_form.version = 2

    def test_func(form):
        return "computed_value"

    decorated_func = cache_form(test_func)

    result1 = decorated_func(mock_form)
    assert result1 == "computed_value"

    result2 = decorated_func(mock_form)
    assert result2 == "computed_value"

    state.request = None


def test_cache_formset_hit():
    mock_request = Mock()
    mock_request.LANGUAGE_CODE = "en-us"
    state.request = mock_request

    mock_flex_form = Mock()
    mock_flex_form.pk = 1
    mock_flex_form.version = 2

    def test_func(flex_form):
        return "computed_value"

    decorated_func = cache_formset(test_func)

    result1 = decorated_func(mock_flex_form)
    assert result1 == "computed_value"

    result2 = decorated_func(mock_flex_form)
    assert result2 == "computed_value"

    state.request = None


def test_cache_form_different_languages():
    mock_request = Mock()
    state.request = mock_request

    mock_form = Mock()
    mock_form.pk = 1
    mock_form.version = 2

    def test_func(form):
        return "computed_value"

    decorated_func = cache_form(test_func)
    mock_request.LANGUAGE_CODE = "en-us"
    result_en = decorated_func(mock_form)
    mock_request.LANGUAGE_CODE = "it-it"
    result_it = decorated_func(mock_form)

    assert result_en == "computed_value"
    assert result_it == "computed_value"

    state.request = None
