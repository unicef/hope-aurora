from unittest.mock import Mock

from django.core.exceptions import ValidationError

import pytest

from aurora.core.models import Validator

HH_SIZE = """if (value.household[0].size_h_c != value.individuals.length){
    "Household size and provided members do not match"
}"""

ONLY_ONE_HEAD = """
if (value.cleaned_data.length===0){
    true
}else{
    var heads = value.cleaned_data.filter(e=>e.relationship_i_c == "head");
    var ret = true;

    if (heads.length==0){
        ret = "At least one member must be set as Head Of Household";
    }else if (heads.length>1){
        ret = "Only one member can be set as Head Of Household";
    }
    ret;
}
"""


@pytest.fixture(autouse=True)
def mock_state():
    from django.contrib.auth.models import AnonymousUser

    from aurora.state import state

    state.request = Mock(user=AnonymousUser())


def test_error_message(db):
    v = Validator(code='"Error"', active=True)
    with pytest.raises(ValidationError) as e:
        v.validate(22)
    assert e.value.messages == ["Error"]


def test_error_dict(db):
    v = Validator(code='{first_name:"Mandatory"}', active=True)
    with pytest.raises(ValidationError) as e:
        v.validate(22)
    assert e.value.message == "Mandatory"


def test_default_error(db):
    v = Validator(code="var a=1;", active=True)
    with pytest.raises(ValidationError) as e:
        v.validate(22)
    assert e.value.message == "Please insert a valid value"


def test_success_true(db):
    v = Validator(code="true", active=True)
    v.validate(22)


def test_form_valid(db):
    v = Validator(code="true", active=True)
    v.validate({"last_name": "Last"})


def test_form_simple(db):
    v = Validator(code="value.last_name.length==3 ? true: 'wrong length';", active=True)
    with pytest.raises(ValidationError) as e:
        v.validate({"last_name": "Last"})
    assert e.value.messages == ["wrong length"]


def test_form_complex(db):
    v = Validator(code='JSON.stringify({last_name: "Invalid"})', active=True)
    with pytest.raises(ValidationError) as e:
        v.validate({"last_name": "Last"})
    assert e.value.message_dict == {"last_name": ["Invalid"]}


@pytest.mark.parametrize(
    "code",
    [
        'var error = (value.last_name.length==3) ? "": "Error"; error',
        '(value.last_name.length==3) ? "": "Error"',
    ],
)
def test_form_fail_custom_message(db, code):
    v = Validator(code=code, active=True)
    with pytest.raises(ValidationError) as e:
        v.validate({"last_name": "Last"})
    assert e.value.messages == ["Error"]


@pytest.mark.parametrize(
    "code",
    [
        'var error = (value.last_name.length==3) ? true: "wrong length"; error',
        '(value.last_name.length==3) ? "": "wrong length"',
    ],
)
def test_form_fail_default_message(db, code):
    v = Validator(code=code, active=True)
    with pytest.raises(ValidationError) as e:
        v.validate({"last_name": "Last"})
    assert e.value.messages == ["wrong length"]


@pytest.mark.parametrize(
    "code",
    [
        'var error = (value.last_name.length==3) ? true: "Error"; error',
        '(value.last_name.length==3) ? true: "Error"',
    ],
)
def test_form_success_custom_message(db, code):
    v = Validator(code=code, active=True)
    v.validate({"last_name": "ABC"})
