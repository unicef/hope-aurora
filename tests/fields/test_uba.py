from unittest.mock import Mock, patch

import pytest
import responses
from constance.test.unittest import override_config
from django.core.exceptions import ValidationError
from strategy_field.utils import fqn
from testutils.factories import FlexFormFieldFactory

from aurora.core.fields import UBANameEnquiryField


@pytest.mark.django_db
@override_config(UBA_TOKEN_URL="https://token")
@override_config(UBA_NAME_ENQUIRY_URL="https://nameenquiry")
@responses.activate
def test_uba_name_enquiry_ok():
    responses._add_from_file(file_path="tests/fields/uba/enquiry_ok.yaml")
    fld = UBANameEnquiryField()
    assert (
        fld.validate(
            {"name": "bank UBA", "code": "000004", "number": "2087008012", "holder_name": "xxxx", "ignore_error": False}
        )
        is None
    )


@pytest.mark.django_db
@override_config(UBA_TOKEN_URL="https://token")
@override_config(UBA_NAME_ENQUIRY_URL="https://nameenquiry")
@responses.activate
@pytest.mark.django_db
def test_uba_name_enquiry_ko_not_matching_name():
    responses._add_from_file(file_path="tests/fields/uba/enquiry_ko_not_matching_name.yaml")
    fld = UBANameEnquiryField()
    with pytest.raises(ValidationError, match="['Account holder name does not match: (xxxx)']"):
        assert fld.validate(
            {
                "name": "bank UBA",
                "code": "000004",
                "number": "2087008012",
                "holder_name": "wrong",
                "ignore_error": False,
            }
        )


@pytest.mark.django_db
@pytest.mark.django_db
def test_uba_name_enquiry_ko_invalid_input():
    fld = UBANameEnquiryField()
    with pytest.raises(ValidationError, match="ValueError: not enough values to unpack"):
        fld.validate({"name": "bank UBA", "code": "000004", "ignore_error": False})


@pytest.mark.django_db
@override_config(UBA_TOKEN_URL="https://token")
@override_config(UBA_NAME_ENQUIRY_URL="https://nameenquiry")
@responses.activate
@pytest.mark.django_db
def test_uba_name_enquiry_ko_invalid_account():
    responses._add_from_file(file_path="tests/fields/uba/enquiry_ko_invalid_account.yaml")
    fld = UBANameEnquiryField()
    with pytest.raises(ValidationError, match="Invalid account number"):
        assert fld.validate(
            {"name": "bank UBA", "code": "000004", "number": "account", "holder_name": "xxxx", "ignore_error": False}
        )


@pytest.mark.django_db
@override_config(UBA_TOKEN_URL="https://token")
@override_config(UBA_NAME_ENQUIRY_URL="https://nameenquiry")
@responses.activate
@pytest.mark.django_db
def test_uba_name_enquiry_generic_invalid():
    responses._add_from_file(file_path="tests/fields/uba/enquiry_generic_invalid.yaml")
    fld = UBANameEnquiryField()
    with pytest.raises(ValidationError, match="['SYSTEM MALFUNCTION: (error 96)']"):
        assert fld.validate(
            {
                "name": "bank UBA",
                "code": "invalid_bank",
                "number": "account",
                "holder_name": "xxxx",
                "ignore_error": False,
            }
        )


@pytest.mark.django_db
@pytest.mark.xfail
@patch("aurora.core.fields.uba.requests.post")
def test_uba_name_enquiry_cannot_reach_server(mock_post):
    mock_post.return_value = Mock(
        status_code=500,
        json=dict,
    )
    fld_c = FlexFormFieldFactory(field_type=fqn(UBANameEnquiryField))
    fld = fld_c.get_instance()
    with pytest.raises(ValidationError, match="Cannot reach UBA server"):
        assert fld.validate(
            {"name": "bank UBA", "code": "bank", "number": "account", "holder_name": "mimmo", "ignore_error": False}
        )
