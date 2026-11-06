from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from strategy_field.utils import fqn
from testutils.factories import FlexFormFieldFactory, FormFactory

from aurora.core.fields import UBAAccountValidationField
from aurora.core.fields.uba_account_validation import (
    ACCOUNT_VALIDATION_RULES,
    UBAAccountValidationMultiWidget,
)
from aurora.core.fields.uba_common import BANKS_CHOICE
from aurora.core.services.uba import (
    AccountValidationResult,
    UBAAccountNotFoundError,
    UBAAPIError,
    UBAAuthError,
    UBAConfigError,
    UBATransportError,
)

pytestmark = pytest.mark.django_db


def make_result(**overrides) -> AccountValidationResult:
    data = {
        "transaction_id": "123",
        "account_name": "xxxx",
        "account_number": "2087008012",
        "bank_code": "000004",
        "account_status": "Active",
        "oper_status": "Name Enquiry successful",
        "raw": {},
        "response_code": "00",
    }
    data.update(overrides)
    return AccountValidationResult(**data)


def make_value(holder_name="xxxx") -> dict:
    return {
        "name": "bank UBA",
        "uba_code": "000004",
        "number": "2087008012",
        "holder_name": holder_name,
        "account_name": "",
        "account_status": "",
        "ignore_error": False,
    }


@patch("aurora.core.services.uba.UBAClient.validate_account")
def test_uba_account_validation_ok(mock_validate):
    mock_validate.return_value = make_result()
    value = make_value()

    assert UBAAccountValidationField().validate(value) is None
    assert value["account_name"] == "xxxx"
    assert value["account_status"] == "Active"


@patch("aurora.core.services.uba.UBAClient.validate_account")
def test_uba_account_validation_name_mismatch(mock_validate):
    mock_validate.return_value = make_result()

    with pytest.raises(ValidationError) as exc:
        UBAAccountValidationField().validate(make_value(holder_name="wrong"))

    assert exc.value.code == "name_mismatch"
    assert "Account holder name does not match: (xxxx)" in exc.value.message


@pytest.mark.parametrize(
    ("overrides", "error_code", "message"),
    [
        ({"response_code": "99"}, "uba_invalid_response_code", "Invalid response code"),
        ({"account_status": "Dormant"}, "uba_invalid_account_status", "Invalid account status"),
        ({"oper_status": "Failed"}, "uba_invalid_account_oper_status", "Invalid account operating status"),
    ],
)
@patch("aurora.core.services.uba.UBAClient.validate_account")
def test_uba_account_validation_response_checks(mock_validate, overrides, error_code, message):
    mock_validate.return_value = make_result(**overrides)

    with pytest.raises(ValidationError) as exc:
        UBAAccountValidationField().validate(make_value())

    assert exc.value.code == error_code
    assert message in exc.value.message


@pytest.mark.django_db
@patch("aurora.core.services.uba.UBAClient.validate_account")
def test_uba_account_validation_allowed_values_can_be_extended(mock_validate):
    mock_validate.return_value = make_result(account_status="Dormant")
    field_c = FlexFormFieldFactory(
        field_type=fqn(UBAAccountValidationField),
        advanced={"account_status_values": ["Dormant"]},
    )
    field = field_c.get_instance()
    value = make_value()

    field.validate(value)

    assert value["account_status"] == "Dormant"


def test_uba_account_validation_ko_invalid_input():
    with pytest.raises(ValidationError, match="ValueError: not enough values to unpack"):
        UBAAccountValidationField().validate({"name": "bank UBA", "uba_code": "000004", "ignore_error": False})


def test_uba_account_validation_compress():
    assert UBAAccountValidationField().compress(["000001", "123", "John"]) == {
        "name": "Sterling Bank",
        "uba_code": "000001",
        "number": "123",
        "holder_name": "John",
        "account_name": "",
        "account_status": "",
        "ignore_error": False,
    }


@patch("aurora.core.services.uba.UBAClient.validate_account")
def test_uba_account_validation_save(mock_validate):
    mock_validate.return_value = make_result()
    flex_form = FormFactory(name="Form1")
    flex_form.fields.get_or_create(
        label="uba",
        required=True,
        defaults={"field_type": UBAAccountValidationField},
    )
    form_class = flex_form.get_form_class()
    form = form_class(data={"uba_0": BANKS_CHOICE[0][0], "uba_1": "2087008012", "uba_2": "xxxx"})

    assert form.is_valid(), form.errors
    assert form.cleaned_data == {
        "uba": {
            "name": "Sterling Bank",
            "uba_code": "000001",
            "number": "2087008012",
            "holder_name": "xxxx",
            "account_name": "xxxx",
            "account_status": "Active",
            "ignore_error": False,
        }
    }


def test_uba_account_validation_multi_widget_decompress():
    widget = UBAAccountValidationMultiWidget()
    assert widget.decompress(None) == [None, None, None]
    assert widget.decompress({"a": 1, "b": 2, "c": 3}) == [1, 2, 3]


def test_account_validation_rule_allowed_accepts_string():
    rule = ACCOUNT_VALIDATION_RULES[0]

    assert rule.allowed({"response_code_values": "00"}) == {"00"}
    assert rule.allowed({"response_code_values": ["00", "01"]}) == {"00", "01"}
    assert rule.allowed({}) == {"00"}


@pytest.mark.parametrize(
    ("exception", "message"),
    [
        (UBAAccountNotFoundError("Invalid account number", code="4"), "Invalid account number"),
        (UBAConfigError("Invalid UBA Api url"), "Invalid UBA Api url"),
        (UBAAuthError("Cannot get UBA token"), "Cannot reach UBA server"),
        (UBATransportError("Cannot reach UBA server"), "Cannot reach UBA server"),
        (UBAAPIError("SYSTEM MALFUNCTION", code="96"), "SYSTEM MALFUNCTION"),
    ],
)
@patch("aurora.core.services.uba.UBAClient.validate_account")
def test_uba_account_validation_api_errors(mock_validate, exception, message):
    mock_validate.side_effect = exception

    with pytest.raises(ValidationError, match=message):
        UBAAccountValidationField().validate(make_value())


@pytest.mark.parametrize(
    "exception", [UBAAuthError("Cannot get UBA token"), UBATransportError("Cannot reach UBA server")]
)
def test_uba_account_validation_can_ignore_connection_errors(exception):
    field_c = FlexFormFieldFactory(
        field_type=fqn(UBAAccountValidationField),
        advanced={"ignore_error": True},
    )
    field = field_c.get_instance()

    with patch("aurora.core.services.uba.UBAClient.validate_account", side_effect=exception):
        assert field.validate(make_value()) is None
