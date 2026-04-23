import pytest
from django import forms
from django.urls import NoReverseMatch

from aurora.core.fields.select import AjaxSelectField
from aurora.core.fields import SelectField
from aurora.core.models import OptionSet


@pytest.fixture
def complex_dataset(db):
    return OptionSet.objects.get_or_create(
        name="complex",
        defaults={
            "data": "1:Rome\r\n2:Milan",
            "separator": ":",
            "pk_col": 0,
            "locale": "en-us",
            "languages": "-,en-us",
        },
    )[0]


@pytest.fixture
def flat(db):
    return OptionSet.objects.get_or_create(
        name="flat",
        defaults={
            "data": "Rome\r\nMilan",
        },
    )[0]


@pytest.fixture
def nested(db):
    return OptionSet.objects.get_or_create(
        name="nested",
        defaults={
            "data": "Rome\r\nMilan",
        },
    )[0]


def test_select_complex(complex_dataset):
    fld = SelectField(datasource="complex")
    assert fld.choices == [("1", "Rome"), ("2", "Milan")]


def test_select_flat(flat):
    fld = SelectField(datasource="flat")
    assert fld.choices == [("rome", "Rome"), ("milan", "Milan")]


def test_select_widget_attrs_and_missing_options(monkeypatch, flat):
    fld = SelectField(datasource="flat", parent_datasource="p1")
    attrs = fld.widget_attrs(fld.widget)
    assert attrs["data-parent"] == "p1"

    monkeypatch.setattr(
        "aurora.core.models.OptionSet.objects.get_from_cache",
        lambda _name: (_ for _ in ()).throw(OptionSet.DoesNotExist()),
    )
    fld.choices = "missing"
    assert fld.choices == []


def test_ajax_select_widget_attrs_and_exceptions(monkeypatch):
    class DummyAjaxField(AjaxSelectField):
        smart_attrs = {"datasource": "source1", "parent_datasource": "p1"}

    fld = DummyAjaxField()
    attrs = fld.widget_attrs(fld.widget)
    assert attrs["data-source"] == "source1"
    assert attrs["data-parent"] == "p1"
    assert "data-ajax--base-url" in attrs
    assert "data-ajax--url-version" in attrs

    monkeypatch.setattr(
        "aurora.core.fields.select.reverse",
        lambda *_a, **_k: (_ for _ in ()).throw(NoReverseMatch("x")),
    )
    monkeypatch.setattr("aurora.core.fields.select.logger.exception", lambda *_a, **_k: None)
    attrs = fld.widget_attrs(fld.widget)
    assert attrs["data-source"] == "source1"


def test_ajax_select_bound_field_and_smart_attrs_path():
    class DummyAjaxField(AjaxSelectField):
        smart_attrs = {"parent_datasource": "p2", "datasource": "ds2"}

    fld = DummyAjaxField()
    assert fld.parent == "p2"
    assert fld.datasource == "ds2"

    class F(forms.Form):
        city = fld

    form = F()
    bound = fld.get_bound_field(form, "city")
    assert bound.field.widget.attrs["data-name"] == "city"
    assert bound.field.widget.attrs["data-label"] == "City"
