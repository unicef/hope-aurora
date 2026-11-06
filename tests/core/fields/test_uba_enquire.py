from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
import responses
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import override_settings
from requests import ReadTimeout
from strategy_field.utils import fqn
from testutils.factories import FlexFormFieldFactory, FormFactory, OptionSetFactory

from aurora.core.fields import UBANameEnquiryField
from aurora.core.fields.uba_common import (
    BANKS_CHOICE,
    BANKS_SORTED_CHOICES,
    UBASelect,
    get_x_auth_cred,
)
from aurora.core.fields.uba_enquire import UBANameEnquiryMultiWidget
from aurora.core.services.uba import UBAAuthError, join_url

if TYPE_CHECKING:
    from aurora.core.models import FlexForm


@pytest.mark.django_db
@override_settings(UBA_TOKEN_URL="https://token", UBA_BASE_URL="https://nameenquiry", UBA_NAME_ENQUIRY_URL="/")
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
@override_settings(UBA_TOKEN_URL="https://token", UBA_BASE_URL="https://nameenquiry", UBA_NAME_ENQUIRY_URL="/")
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
@override_settings(UBA_TOKEN_URL="https://token", UBA_BASE_URL="https://nameenquiry", UBA_NAME_ENQUIRY_URL="/")
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
@override_settings(UBA_TOKEN_URL="https://token", UBA_BASE_URL="https://nameenquiry", UBA_NAME_ENQUIRY_URL="/")
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
@patch("aurora.core.services.uba.requests.post")
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
@override_settings(UBA_TOKEN_URL="---")
def test_uba_name_missing_schema():
    cache.clear()
    fld_c = FlexFormFieldFactory(field_type=fqn(UBANameEnquiryField), advanced={"ignore_error": False})
    fld: UBANameEnquiryField = fld_c.get_instance()
    with pytest.raises(ValidationError, match="Invalid UBA Api url"):
        assert fld.validate(
            {"name": "bank UBA", "uba_code": "bank", "number": "account", "holder_name": "mimmo", "ignore_error": False}
        )


@pytest.mark.django_db
@patch("aurora.core.services.uba.requests.post", side_effect=ReadTimeout)
def test_uba_name_connection_error(mock_post):
    fld_c = FlexFormFieldFactory(field_type=fqn(UBANameEnquiryField), advanced={"ignore_error": False})
    fld = fld_c.get_instance()
    with pytest.raises(ValidationError, match="Cannot reach UBA server"):
        assert fld.validate(
            {"name": "bank UBA", "uba_code": "bank", "number": "account", "holder_name": "mimmo", "ignore_error": False}
        )


@pytest.mark.django_db
@override_settings(UBA_TOKEN_URL="https://token", UBA_BASE_URL="https://nameenquiry", UBA_NAME_ENQUIRY_URL="/")
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


@pytest.mark.django_db
def test_uba_select_no_optionset():
    widget = UBASelect()
    assert widget.attrs["choices"] == BANKS_SORTED_CHOICES


@pytest.mark.django_db
def test_uba_name_enquiry_multi_widget_decompress():
    widget = UBANameEnquiryMultiWidget()
    assert widget.decompress(None) == [None, None, None, None, None]
    assert widget.decompress({"a": 1, "b": 2}) == [1, 2]


def test_join_url():
    assert join_url("https://base", "/endpoint") == "https://base/endpoint"
    assert join_url("https://base/", "endpoint") == "https://base/endpoint"
    assert join_url("https://base/prefix", "/endpoint") == "https://base/prefix/endpoint"
    assert join_url("", "/endpoint") == "/endpoint"


def test_get_x_auth_cred():
    assert get_x_auth_cred("1234") == b"0000000031323334"


@pytest.mark.django_db
def test_uba_select_with_optionset():
    OptionSetFactory(name="test-uba-options", data="001;Bank A\r\n002;Bank B")

    choices = list(UBASelect({"optionset_name": "test-uba-options"}).attrs["choices"])

    assert choices == [("001", "Bank A"), ("002", "Bank B")]


@pytest.mark.django_db
def test_uba_multi_widget_media():
    assert "select2/select2.min.css" in str(UBANameEnquiryMultiWidget().media)


@pytest.mark.django_db
def test_uba_name_enquiry_ignore_error_without_flex_field():
    assert UBANameEnquiryField()._ignore_error() is False


@pytest.mark.django_db
def test_uba_name_enquiry_can_ignore_connection_errors():
    fld_c = FlexFormFieldFactory(field_type=fqn(UBANameEnquiryField), advanced={"ignore_error": True})
    fld = fld_c.get_instance()

    with patch("aurora.core.services.uba.UBAClient.name_enquiry", side_effect=UBAAuthError):
        assert (
            fld.validate(
                {
                    "name": "bank UBA",
                    "uba_code": "bank",
                    "number": "account",
                    "holder_name": "mimmo",
                    "ignore_error": True,
                }
            )
            is None
        )
