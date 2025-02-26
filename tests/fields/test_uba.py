from unittest.mock import Mock, patch

import pytest
import responses
from django.core.exceptions import ValidationError
from responses import _recorder

from aurora.core.fields import UBANameEnquiryField


@pytest.mark.django_db
# @patch("aurora.core.fields.uba.requests.post")
@_recorder.record(file_path="tests/fields/uba/responses/enquire_ok.yaml")
@responses.activate
def test_uba_name_enquiry_ok():
    # mock_post.return_value = Mock(
    #     status_code=200,
    #     json=lambda: {
    #         "message": "operation successful",
    #         "data": {
    #             "lookupParam": "100001241210170958777131925463_DANIEL ADEBAYO ADEDOYIN_22000000051_3",
    #             "beneficiaryAccountNumber": "8168208035",
    #             "beneficiaryBankCode": "100004",
    #             "beneficiaryAccountName": "DANIEL ADEBAYO ADEDOYIN",
    #         },
    #         "code": "00",
    #         "error": "",
    #     },
    # )
    # responses._add_from_file(file_path="tests/fields/uba/responses/enquire_ok.yaml")
    fld = UBANameEnquiryField()
    assert fld.validate("bank|account|xxxx") is None


# @pytest.mark.django_db
# @patch("aurora.core.fields.uba.requests.post")
# def test_uba_name_enquiry_ko_not_matching_name(mock_post):
#     mock_post.return_value = Mock(
#         status_code=200,
#         json=lambda: {
#             "message": "operation successful",
#             "data": {
#                 "lookupParam": "100001241210170958777131925463_DANIEL ADEBAYO ADEDOYIN_22000000051_3",
#                 "beneficiaryAccountNumber": "8168208035",
#                 "beneficiaryBankCode": "100004",
#                 "beneficiaryAccountName": "DANIEL ADEBAYO ADEDOYIN",
#             },
#             "code": "00",
#             "error": "",
#         },
#     )
#     fld = UBANameEnquiryField()
#     with pytest.raises(ValidationError, match="Wrong account holder mimmo"):
#         assert fld.validate("bank|account|mimmo") is None
#
#
# @pytest.mark.django_db
# @patch("aurora.core.fields.uba.requests.post")
# @pytest.mark.override_config()
# def test_uba_name_enquiry_ok_not_matching_name(mock_post):
#     mock_post.return_value = Mock(
#         status_code=200,
#         json=lambda: {
#             "message": "operation successful",
#             "data": {
#                 "lookupParam": "100001241210170958777131925463_DANIEL ADEBAYO ADEDOYIN_22000000051_3",
#                 "beneficiaryAccountNumber": "8168208035",
#                 "beneficiaryBankCode": "100004",
#                 "beneficiaryAccountName": "DANIEL ADEBAYO ADEDOYIN",
#             },
#             "code": "00",
#             "error": "",
#         },
#     )
#     fld = UBANameEnquiryField()
#     assert fld.validate("bank|account|mimmo") is None
#
#
# def test_uba_name_enquiry_ko_value_error():
#     fld = UBANameEnquiryField()
#     with pytest.raises(ValidationError, match="ValueError: not enough values to unpack"):
#         fld.validate("only_one_value")
#
#
# @pytest.mark.django_db
# @patch("aurora.core.fields.uba.requests.post")
# def test_uba_name_enquiry_error_status_code(mock_post):
#     mock_post.return_value = Mock(
#         status_code=400,
#         json=lambda: {
#             "message": "operation successful",
#             "data": {
#                 "lookupParam": "100001241210170958777131925463_DANIEL ADEBAYO ADEDOYIN_22000000051_3",
#                 "beneficiaryAccountNumber": "8168208035",
#                 "beneficiaryBankCode": "100004",
#                 "beneficiaryAccountName": "DANIEL ADEBAYO ADEDOYIN",
#             },
#             "code": "00",
#             "error": "",
#         },
#     )
#     fld = UBANameEnquiryField()
#     with pytest.raises(ValidationError, match="Error 400"):
#         assert fld.validate("bank|account|mimmo") is None
#
#
# @pytest.mark.django_db
# @patch("aurora.core.fields.uba.requests.post")
# def test_uba_name_enquiry_error_500(mock_post):
#     mock_post.return_value = Mock(
#         status_code=500,
#         reason="Internal Server Error",
#         json=lambda: {
#             "message": "operation successful",
#             "data": {
#                 "lookupParam": "100001241210170958777131925463_DANIEL ADEBAYO ADEDOYIN_22000000051_3",
#                 "beneficiaryAccountNumber": "8168208035",
#                 "beneficiaryBankCode": "100004",
#                 "beneficiaryAccountName": "DANIEL ADEBAYO ADEDOYIN",
#             },
#             "code": "00",
#             "error": "",
#         },
#     )
#     fld = UBANameEnquiryField()
#     with pytest.raises(ValidationError, match="Internal Server Error"):
#         assert fld.validate("bank|account|mimmo") is None
#
#
# @pytest.mark.django_db
# @patch("aurora.core.fields.uba.requests.post")
# def test_uba_name_enquiry_error_error(mock_post):
#     mock_post.return_value = Mock(
#         status_code=400,
#         json=lambda: {
#             "message": "operation successful",
#             "data": {
#                 "lookupParam": "100001241210170958777131925463_DANIEL ADEBAYO ADEDOYIN_22000000051_3",
#                 "beneficiaryAccountNumber": "8168208035",
#                 "beneficiaryBankCode": "100004",
#                 "beneficiaryAccountName": "DANIEL ADEBAYO ADEDOYIN",
#             },
#             "code": "00",
#             "error": "Bad Request",
#         },
#     )
#     fld = UBANameEnquiryField()
#     with pytest.raises(ValidationError, match="Bad Request"):
#         assert fld.validate("bank|account|mimmo") is None
