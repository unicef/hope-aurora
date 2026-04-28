import json

import pytest
from django.core.exceptions import ValidationError

from aurora.core.models import OptionSet


def test_base(db):
    obj = OptionSet.objects.create(
        name="italian_locations",
        data="Rome\r\nMilan",
        separator="",
        pk_col=0,
        parent_col=-1,
        locale="en-us",
        languages="en-us",
    )
    assert list(obj.as_choices()) == [("rome", "Rome"), ("milan", "Milan")]
    assert obj.as_json() == [
        {"label": "Rome", "parent": None, "pk": "rome"},
        {"label": "Milan", "parent": None, "pk": "milan"},
    ]


def test_complex(db):
    obj = OptionSet.objects.create(
        name="italian_locations2",
        data="1:Rome\r\n2:Milan",
        separator=":",
        pk_col=0,
        parent_col=-1,
        locale="en-us",
        languages="_,en-us",
    )
    assert list(obj.as_choices()) == [("1", "Rome"), ("2", "Milan")]
    assert obj.as_json() == [
        {"label": "Rome", "parent": None, "pk": "1"},
        {"label": "Milan", "parent": None, "pk": "2"},
    ]


def test_parent(db):
    obj = OptionSet.objects.create(
        name="italian_locations3",
        data="1:1:Rome\r\n2:1:Milan",
        separator=":",
        pk_col=0,
        parent_col=1,
        locale="en-us",
        languages="-,-,en-us",
    )
    assert list(obj.as_choices()) == [("1", "Rome"), ("2", "Milan")]
    assert obj.as_json() == [
        {"label": "Rome", "parent": "1", "pk": "1"},
        {"label": "Milan", "parent": "1", "pk": "2"},
    ]


def test_view_base(db, django_app):
    obj = OptionSet.objects.create(
        name="locations-1",
        data="Rome\r\nMilan",
        separator="",
        pk_col=0,
        parent_col=-1,
        locale="en-us",
        languages="en-us",
    )
    res = django_app.get(obj.get_api_url())
    assert json.loads(res.content) == {
        "results": [
            {"id": "rome", "parent": None, "text": "Rome"},
            {"id": "milan", "parent": None, "text": "Milan"},
        ]
    }


def test_view_complex(db, django_app):
    obj = OptionSet.objects.create(
        name="locations-2",
        data="1:Rome\r\n2:Milan",
        separator=":",
        pk_col=0,
        parent_col=-1,
        locale="en-us",
        languages="_,en-us",
    )
    res = django_app.get(obj.get_api_url())
    assert json.loads(res.content) == {
        "results": [
            {"id": "1", "parent": None, "text": "Rome"},
            {"id": "2", "parent": None, "text": "Milan"},
        ]
    }


def test_view_parent(db, django_app):
    obj = OptionSet.objects.create(
        name="locations-3",
        data="1:1:Rome\r\n2:1:Milan",
        separator=":",
        pk_col=0,
        parent_col=1,
        locale="en-us",
        languages="-,-,en-us",
    )
    res = django_app.get(obj.get_api_url())
    assert json.loads(res.content) == {
        "results": [
            {"id": "1", "parent": "1", "text": "Rome"},
            {"id": "2", "parent": "1", "text": "Milan"},
        ]
    }


def test_pk_col_out_of_bounds_fallback(db):
    obj = OptionSet.objects.create(
        name="test_bounds",
        data="Rome\r\nMilan",
        pk_col=5,
        locale="en-us",
        languages="en-us",
    )
    result = obj.get_data("en-us")
    assert result[0]["pk"] == "rome"


def test_parent_col_handling(db):
    obj = OptionSet.objects.create(
        name="test_parent",
        data="parent1:child1\r\nparent2:child2",
        separator=":",
        pk_col=1,
        parent_col=0,
        locale="en-us",
        languages="_,en-us",
    )
    result = obj.get_data("en-us")
    assert result[0]["parent"] == "parent1"


def test_parent_col_disabled(db):
    obj = OptionSet.objects.create(
        name="test_parent_disabled",
        data="parent1:child1\r\nparent2:child2",
        separator=":",
        pk_col=1,
        parent_col=-1,
        locale="en-us",
        languages="_,en-us",
    )
    result = obj.get_data("en-us")
    assert result[0]["parent"] is None


def test_multilingual_columns(db):
    obj = OptionSet.objects.create(
        name="test_multi",
        data="#id:en:fr:de\r\n1:one:un:eins\r\n2:two:deux:zwei",
        separator=":",
        pk_col=0,
        locale="en",
        languages="id,en,fr,de",
    )

    assert [r["label"] for r in obj.get_data("fr")] == ["un", "deux"]
    assert [r["label"] for r in obj.get_data("de")] == ["eins", "zwei"]
    assert [r["label"] for r in obj.get_data("en")] == ["one", "two"]


def test_clean_validation_error(db):
    obj = OptionSet(
        name="test",
        data="test",
        locale="en-us",
        languages="it-it",
    )
    with pytest.raises(ValidationError):
        obj.clean()


def test_as_choices_with_language_column(db):
    obj = OptionSet.objects.create(
        name="test",
        data="en:English\r\nit:Italiano",
        separator=":",
        pk_col=0,
        locale="en-us",
        languages="_,en-us",
    )
    assert list(obj.as_choices("en-us")) == [("en", "English"), ("it", "Italiano")]
