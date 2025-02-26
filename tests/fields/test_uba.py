from unittest.mock import patch, Mock

import pytest
import responses
from constance.test.unittest import override_config
from django.core.exceptions import ValidationError

from aurora.core.fields import UBANameEnquiryField


@pytest.mark.django_db
@override_config(UBA_TOKEN_URL="https://token")
@override_config(UBA_NAME_ENQUIRY_URL="https://nameenquiry")
@responses.activate
def test_uba_name_enquiry_ok():
    responses._add_from_file(file_path="tests/fields/uba/enquiry_ok.yaml")
    fld = UBANameEnquiryField()
    assert (
        fld.validate({"institution_code": "000004", "account_number": "2087008012", "account_holder": "xxxx"}) is None
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
        assert fld.validate({"institution_code": "000004", "account_number": "2087008012", "account_holder": "wrong"})


@pytest.mark.django_db
@pytest.mark.django_db
def test_uba_name_enquiry_ko_invalid_input():
    fld = UBANameEnquiryField()
    with pytest.raises(ValidationError, match="ValueError: not enough values to unpack"):
        fld.validate({"institution_code": "000004"})


@pytest.mark.django_db
@override_config(UBA_TOKEN_URL="https://token")
@override_config(UBA_NAME_ENQUIRY_URL="https://nameenquiry")
@responses.activate
@pytest.mark.django_db
def test_uba_name_enquiry_ko_invalid_account():
    responses._add_from_file(file_path="tests/fields/uba/enquiry_ko_invalid_account.yaml")
    fld = UBANameEnquiryField()
    with pytest.raises(ValidationError, match="Invalid account number"):
        assert fld.validate({"institution_code": "000004", "account_number": "account", "account_holder": "xxxx"})


@pytest.mark.django_db
@override_config(UBA_TOKEN_URL="https://token")
@override_config(UBA_NAME_ENQUIRY_URL="https://nameenquiry")
@responses.activate
@pytest.mark.django_db
def test_uba_name_enquiry_generic_invalid():
    responses._add_from_file(file_path="tests/fields/uba/enquiry_generic_invalid.yaml")
    fld = UBANameEnquiryField()
    with pytest.raises(ValidationError, match="['SYSTEM MALFUNCTION: (error 96)']"):
        assert fld.validate({"institution_code": "invalid_bank", "account_number": "account", "account_holder": "xxxx"})


@pytest.mark.django_db
@patch("aurora.core.fields.uba.requests.post")
@pytest.mark.django_db
def test_uba_name_enquiry_cannot_reach_server(mock_post):
    mock_post.return_value = Mock(
        status_code=401,
        json=dict,
    )
    fld = UBANameEnquiryField()
    with pytest.raises(ValidationError, match="Cannot reach UBA server"):
        assert fld.validate({"institution_code": "bank", "account_number": "account", "account_holder": "mimmo"})
