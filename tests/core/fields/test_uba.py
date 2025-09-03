from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
import responses
from constance.test.unittest import override_config
from django.core.cache import cache
from django.core.exceptions import ValidationError
from requests import ReadTimeout
from strategy_field.utils import fqn
from testutils.factories import FlexFormFieldFactory, FormFactory

from aurora.core.fields import UBANameEnquiryField
from aurora.core.fields.uba import BANKS_CHOICE

if TYPE_CHECKING:
    from aurora.core.models import FlexForm


@pytest.mark.django_db
@override_config(UBA_TOKEN_URL="https://token")
@override_config(UBA_NAME_ENQUIRY_URL="https://nameenquiry")
@responses.activate
def test_uba_name_enquiry_ok():
    responses._add_from_file(file_path=Path(__file__).parent / "uba/enquiry_ok.yaml")
    fld = UBANameEnquiryField()
    assert (
        fld.validate(
            {
                "name": "bank UBA",
                "uba_code": "000004",
                "number": "2087008012",
                "holder_name": "xxxx",
                "ignore_error": False,
            }
        )
        is None
    )


@pytest.mark.django_db
@override_config(UBA_TOKEN_URL="https://token")
@override_config(UBA_NAME_ENQUIRY_URL="https://nameenquiry")
@responses.activate
@pytest.mark.django_db
def test_uba_name_enquiry_ko_not_matching_name():
    responses._add_from_file(file_path=Path(__file__).parent / "uba/enquiry_ko_not_matching_name.yaml")
    fld = UBANameEnquiryField()
    with pytest.raises(ValidationError, match="['Account holder name does not match: (xxxx)']"):
        assert fld.validate(
            {
                "name": "bank UBA",
                "uba_code": "000004",
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
        fld.validate({"name": "bank UBA", "uba_code": "000004", "ignore_error": False})


@pytest.mark.django_db
@override_config(UBA_TOKEN_URL="https://token")
@override_config(UBA_NAME_ENQUIRY_URL="https://nameenquiry")
@responses.activate
@pytest.mark.django_db
def test_uba_name_enquiry_ko_invalid_account():
    responses._add_from_file(file_path=Path(__file__).parent / "uba/enquiry_ko_invalid_account.yaml")
    fld = UBANameEnquiryField()
    with pytest.raises(ValidationError, match="Invalid account number"):
        assert fld.validate(
            {
                "name": "bank UBA",
                "uba_code": "000004",
                "number": "account",
                "holder_name": "xxxx",
                "ignore_error": False,
            }
        )


@pytest.mark.django_db
@override_config(UBA_TOKEN_URL="https://token")
@override_config(UBA_NAME_ENQUIRY_URL="https://nameenquiry")
@responses.activate
@pytest.mark.django_db
def test_uba_name_enquiry_generic_invalid():
    responses._add_from_file(file_path=Path(__file__).parent / "uba/enquiry_generic_invalid.yaml")
    fld = UBANameEnquiryField()
    with pytest.raises(ValidationError, match="['SYSTEM MALFUNCTION: (error 96)']"):
        assert fld.validate(
            {
                "name": "bank UBA",
                "uba_code": "invalid_bank",
                "number": "account",
                "holder_name": "xxxx",
                "ignore_error": False,
            }
        )


@pytest.mark.django_db
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
            {"name": "bank UBA", "uba_code": "bank", "number": "account", "holder_name": "mimmo", "ignore_error": False}
        )


@pytest.mark.django_db
@override_config(UBA_TOKEN_URL="---")
def test_uba_name_missing_schema():
    cache.clear()
    fld_c = FlexFormFieldFactory(field_type=fqn(UBANameEnquiryField), advanced={"ignore_error": False})
    fld: UBANameEnquiryField = fld_c.get_instance()
    with pytest.raises(ValidationError, match="Invalid UBA Api url"):
        assert fld.validate(
            {"name": "bank UBA", "uba_code": "bank", "number": "account", "holder_name": "mimmo", "ignore_error": False}
        )


@pytest.mark.django_db
@patch("aurora.core.fields.uba.requests.post", side_effect=ReadTimeout)
def test_uba_name_connection_error(mock_post):
    fld_c = FlexFormFieldFactory(field_type=fqn(UBANameEnquiryField), advanced={"ignore_error": False})
    fld = fld_c.get_instance()
    with pytest.raises(ValidationError, match="Cannot reach UBA server"):
        assert fld.validate(
            {"name": "bank UBA", "uba_code": "bank", "number": "account", "holder_name": "mimmo", "ignore_error": False}
        )


@pytest.mark.django_db
@override_config(UBA_TOKEN_URL="https://token")
@override_config(UBA_NAME_ENQUIRY_URL="https://nameenquiry")
@responses.activate
def test_uba_save():
    responses._add_from_file(file_path=Path(__file__).parent / "uba/enquiry_ok.yaml")
    flex_frm: FlexForm = FormFactory(name="Form1")
    flex_frm.fields.get_or_create(label="uba", required=True, defaults={"field_type": UBANameEnquiryField})
    form_class = flex_frm.get_form_class()
    form = form_class(data={"uba_0": BANKS_CHOICE[0][0], "uba_1": "xxxx", "uba_2": "xxxx"})
    assert form.is_valid(), form.errors
    assert form.cleaned_data == {
        "uba": {
            "name": "Sterling Bank",
            "uba_code": "000001",
            "number": "xxxx",
            "holder_name": "xxxx",
            "ignore_error": False,
        }
    }
