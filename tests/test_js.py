import pytest
from django.core.exceptions import ValidationError
from freezegun import freeze_time

from aurora.core.js import DukPYValidator

ENGINES = [DukPYValidator]


@pytest.mark.parametrize("engine_class", ENGINES)
def test_js_validator_error(engine_class):
    engine = engine_class("value.last_name.length==3 ? true: 'wrong length';")
    with pytest.raises(ValidationError, match="wrong length"):
        engine.validate({"last_name": "Last"})


@pytest.mark.parametrize("engine_class", ENGINES)
def test_js_validator_success(engine_class):
    engine = engine_class("value.last_name.length==3 ? true: 'wrong length';")
    assert engine.validate({"last_name": "Las"})


@pytest.mark.parametrize("input_value", [33, {"last_name": "Last"}])
@pytest.mark.parametrize("engine_class", ENGINES)
def test_true(engine_class, input_value):
    engine = engine_class("true")
    assert engine.validate(input_value)


@pytest.mark.parametrize("input_value", [33, {"last_name": "Last"}])
@pytest.mark.parametrize("engine_class", ENGINES)
def test_false(engine_class, input_value):
    engine = engine_class("false")
    with pytest.raises(ValidationError, match="Please insert a valid value"):
        engine.validate(input_value)


@pytest.mark.parametrize(
    "code",
    [
        'var error = (value.last_name.length==3) ? "": "Error"; error',
        '(value.last_name.length==3) ? "": "Error"',
    ],
)
@pytest.mark.parametrize("engine_class", ENGINES)
def test_form_fail_custom_message(engine_class, code):
    engine = engine_class(code)
    with pytest.raises(ValidationError) as e:
        engine.validate({"last_name": "Last"})
    assert e.value.messages == ["Error"]


@pytest.mark.parametrize("engine_class", ENGINES)
def test_form_complex(engine_class):
    engine = engine_class('JSON.stringify({last_name: "Invalid"})')
    with pytest.raises(ValidationError) as e:
        engine.validate({"last_name": "Last"})
    assert e.value.message_dict == {"last_name": ["Invalid"]}


@pytest.mark.parametrize("engine_class", ENGINES)
def test_error_message(engine_class):
    engine = engine_class('"Error"')
    with pytest.raises(ValidationError) as e:
        engine.validate(22)
    assert e.value.messages == ["Error"]


@pytest.mark.parametrize("engine_class", ENGINES)
def test_error_dict(engine_class):
    engine = engine_class('{first_name:"Mandatory"}')
    with pytest.raises(ValidationError) as e:
        engine.validate(22)
    assert e.value.message == "Mandatory"


@pytest.mark.parametrize("engine_class", ENGINES)
def test_library_getage(engine_class):
    engine = engine_class("""
if (value > dateutil.getAge("2020-01-01", "2020-01-02")){
    "Error";
}
    """)
    with pytest.raises(ValidationError, match="Error"):
        engine.validate(22)


@freeze_time("2020-01-01")
@pytest.mark.parametrize("engine_class", ENGINES)
def test_library_is_child(engine_class):
    engine = engine_class("""
if (_.is_child("2020-01-20")){
    "Error";
}
    """)
    with pytest.raises(ValidationError, match="Error"):
        engine.validate(22)
