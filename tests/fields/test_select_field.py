import pytest

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
