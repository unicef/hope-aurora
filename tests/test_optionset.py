import json

from aurora.core.models import OptionSet


def test_base(db):
    obj = OptionSet(
        name="italian_locations",
        data="Rome\r\nMilan",
        pk_col=0,
        locale="en-us",
        languages="-,-,en-us",
    )
    obj.clean()
    assert list(obj.as_choices()) == [("rome", "Rome"), ("milan", "Milan")]
    assert obj.as_json() == [
        {"label": "Rome", "parent": None, "pk": "rome"},
        {"label": "Milan", "parent": None, "pk": "milan"},
    ]


def test_complex(db):
    obj = OptionSet(
        name="italian_locations",
        data="1:Rome\r\n2:Milan",
        separator=":",
        pk_col=0,
        locale="en-us",
        languages="-,en-us",
    )
    obj.clean()
    assert list(obj.as_choices()) == [("1", "Rome"), ("2", "Milan")]
    assert obj.as_json() == [
        {"label": "Rome", "parent": None, "pk": "1"},
        {"label": "Milan", "parent": None, "pk": "2"},
    ]


def test_parent(db):
    obj = OptionSet(
        name="italian_locations",
        data="1:1:Rome\r\n2:1:Milan",
        parent_col=1,
        separator=":",
        locale="en-us",
        languages="-,-,en-us",
    )
    obj.clean()
    assert list(obj.as_choices()) == [("1", "Rome"), ("2", "Milan")]
    assert obj.as_json() == [
        {"label": "Rome", "parent": "1", "pk": "1"},
        {"label": "Milan", "parent": "1", "pk": "2"},
    ]


def test_view_base(db, django_app):
    obj = OptionSet.objects.create(
        name="locations-1",
        data="Rome\r\nMilan",
        pk_col=0,
        locale="en-us",
        languages="en-us",
    )
    url = obj.get_api_url()
    res = django_app.get(url)
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
        locale="en-us",
        languages="-,en-us",
    )
    url = obj.get_api_url()
    res = django_app.get(url)
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
    url = obj.get_api_url()
    res = django_app.get(url)
    assert json.loads(res.content) == {
        "results": [
            {"id": "1", "parent": "1", "text": "Rome"},
            {"id": "2", "parent": "1", "text": "Milan"},
        ]
    }
