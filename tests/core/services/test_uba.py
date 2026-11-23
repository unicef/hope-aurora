from unittest.mock import Mock, patch

import pytest
from django.core.cache import cache
from django.test import override_settings
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import MissingSchema, ReadTimeout

from aurora.core.services.uba import (
    TOKEN_CACHE_KEY,
    AccountValidationResult,
    UBAAPIError,
    UBAAuthError,
    UBAClient,
    UBAConfig,
    UBAConfigError,
    UBATransportError,
    join_url,
    status_message,
)

UBA_SETTINGS = {
    "UBA_BASE_URL": "https://uba",
    "UBA_TOKEN_URL": "https://uba/token",
    "UBA_NAME_ENQUIRY_URL": "/name-enquiry",
    "UBA_ACCOUNT_VALIDATION_URL": "/account-validation",
    "UBA_APPL_CODE": "appl",
    "UBA_CLIENT_NO": "client",
    "UBA_X_AUTH_CRED": "cred",
    "UBA_CONSUMER_KEY": "consumer",
    "UBA_CONSUMER_SECRET": "secret",
}

TOKEN_RESPONSE = {"token_type": "Bearer", "access_token": "abc", "expires_in": 900}
VALIDATION_RESPONSE = {
    "response": {
        "transactionId": "txn-1",
        "accountName": "John Doe",
        "accountNumber": "2087008012",
        "bankCode": "000004",
        "accountStatus": "Active",
        "accountOperStatus": "Name Enquiry successful",
        "responseCode": "00",
        "sessionID": "session-1",
        "bankVerificationNumber": "bvn",
        "kycLevel": "3",
    }
}


@pytest.fixture(autouse=True)
def _clear_token_cache():
    cache.clear()
    yield
    cache.clear()


def response(*, status: int = 200, json_data=None, json_error: Exception | None = None) -> Mock:
    result = Mock(status_code=status)
    if json_error:
        result.json.side_effect = json_error
    else:
        result.json.return_value = TOKEN_RESPONSE if json_data is None else json_data
    return result


def test_status_message():
    assert status_message("00") == "Success"
    assert status_message(96) == "System malfunction"
    assert status_message("999") == "Unknown error"
    assert status_message(None) == "Unknown error"
    assert status_message(None, default="Custom") == "Custom"


def test_join_url():
    assert join_url("", "endpoint") == "endpoint"
    assert join_url("https://uba", "endpoint") == "https://uba/endpoint"


@override_settings(**UBA_SETTINGS)
def test_config_from_settings():
    config = UBAConfig.from_settings()

    assert config.token_url == "https://uba/token"
    assert config.name_enquiry_url == "https://uba/name-enquiry"
    assert config.account_validation_url == "https://uba/account-validation"
    assert config.consumer_key == "consumer"


def test_get_access_token_from_cache():
    cache.set(TOKEN_CACHE_KEY, "Bearer cached")

    with patch("aurora.core.services.uba.requests.post") as post:
        assert UBAClient().get_access_token() == "Bearer cached"
        post.assert_not_called()


@override_settings(**UBA_SETTINGS)
def test_get_access_token_force_refresh():
    cache.set(TOKEN_CACHE_KEY, "Bearer cached")

    with patch("aurora.core.services.uba.requests.post", return_value=response()) as post:
        assert UBAClient().get_access_token(force=True) == "Bearer abc"

    post.assert_called_once()
    assert cache.get(TOKEN_CACHE_KEY) == "Bearer abc"


@override_settings(**UBA_SETTINGS)
def test_get_access_token_invalid_url():
    with (
        patch("aurora.core.services.uba.requests.post", side_effect=MissingSchema),
        pytest.raises(UBAConfigError, match="Invalid UBA Api url"),
    ):
        UBAClient().get_access_token()


@override_settings(**UBA_SETTINGS)
@pytest.mark.parametrize(
    "first",
    [
        ReadTimeout(),
        RequestsConnectionError(),
        response(status=401),
        response(json_data={"unexpected": "payload"}),
    ],
)
def test_get_access_token_retries(first):
    with patch("aurora.core.services.uba.requests.post", side_effect=[first, response()]):
        assert UBAClient().get_access_token() == "Bearer abc"


@override_settings(**UBA_SETTINGS)
def test_get_access_token_gives_up():
    bad = response(json_data={"unexpected": "payload"})

    with (
        patch("aurora.core.services.uba.requests.post", side_effect=[bad, bad]),
        pytest.raises(UBAAuthError, match="Cannot get UBA token"),
    ):
        UBAClient().get_access_token()


@override_settings(**UBA_SETTINGS)
def test_get_access_token_without_expiry():
    payload = {"token_type": "Bearer", "access_token": "abc"}

    with patch("aurora.core.services.uba.requests.post", return_value=response(json_data=payload)):
        assert UBAClient().get_access_token() == "Bearer abc"

    assert cache.get(TOKEN_CACHE_KEY) == "Bearer abc"


@override_settings(**UBA_SETTINGS)
def test_headers_include_checksum():
    headers = UBAClient()._headers(access_code="Bearer x", checksum="checksum")

    assert headers == {
        "AccessCode": "Bearer x",
        "Applcode": "appl",
        "Clientno": "client",
        "X-Auth-Cred": "cred",
        "Checksum": "checksum",
    }


def test_account_validation_result_from_response():
    result = AccountValidationResult.from_response(VALIDATION_RESPONSE)

    assert result.account_name == "John Doe"
    assert result.response_code == "00"
    assert result.session_id == "session-1"
    assert result.bank_verification_number == "bvn"
    assert result.kyc_level == "3"
    assert result.raw == VALIDATION_RESPONSE


def test_account_validation_result_success_without_response_code():
    result = AccountValidationResult.from_response(
        {"accountName": "John Doe", "accountNumber": "2087008012", "bankCode": "000004"},
    )

    assert result.response_code is None
    assert result.account_number == "2087008012"


def test_account_validation_result_success_from_oper_status():
    result = AccountValidationResult.from_response(
        {"accountOperStatus": "Name Enquiry successful"},
        fallback_account_number="2087008012",
        fallback_bank_code="000004",
    )

    assert result.account_number == "2087008012"
    assert result.bank_code == "000004"
    assert result.account_name == ""


def test_account_validation_result_failure():
    payload = {"response": {"responseCode": "99", "accountOperStatus": ""}}

    with pytest.raises(UBAAPIError) as exc:
        AccountValidationResult.from_response(payload)

    assert exc.value.code == "99"
    assert exc.value.message == "Failed"
    assert exc.value.payload == payload


def test_account_validation_result_failure_uses_oper_status():
    payload = {"responseCode": "999", "accountOperStatus": "Dormant account"}

    with pytest.raises(UBAAPIError) as exc:
        AccountValidationResult.from_response(payload)

    assert exc.value.message == "Dormant account"


@override_settings(**UBA_SETTINGS)
def test_name_enquiry_transport_error():
    with (
        patch("aurora.core.services.uba.UBAClient.get_access_token", return_value="Bearer x"),
        patch("aurora.core.services.uba.requests.post", side_effect=ReadTimeout),
        pytest.raises(UBATransportError, match="Cannot reach UBA server"),
    ):
        UBAClient().name_enquiry(bank_code="000004", account_number="2087008012")


@override_settings(**UBA_SETTINGS)
def test_name_enquiry_invalid_url():
    with (
        patch("aurora.core.services.uba.UBAClient.get_access_token", return_value="Bearer x"),
        patch("aurora.core.services.uba.requests.post", side_effect=MissingSchema),
        pytest.raises(UBAConfigError, match="Invalid UBA Api url"),
    ):
        UBAClient().name_enquiry(bank_code="000004", account_number="2087008012")


@override_settings(**UBA_SETTINGS)
def test_name_enquiry_refreshes_token_on_auth_error():
    with (
        patch("aurora.core.services.uba.UBAClient.get_access_token", side_effect=[UBAAuthError, "Bearer x"]) as token,
        patch(
            "aurora.core.services.uba.requests.post",
            return_value=response(json_data={"errorFlag": "false", "statusCode": "0", "customerName": "John"}),
        ),
    ):
        result = UBAClient().name_enquiry(bank_code="000004", account_number="2087008012")

    assert result.customer_name == "John"
    assert token.call_args_list[0].kwargs["force"] is False
    assert token.call_args_list[1].kwargs["force"] is True


@override_settings(**UBA_SETTINGS)
def test_validate_account_success():
    with (
        patch("aurora.core.services.uba.UBAClient.get_access_token", return_value="Bearer x"),
        patch("aurora.core.services.uba.requests.post", return_value=response(json_data=VALIDATION_RESPONSE)) as post,
    ):
        result = UBAClient().validate_account(
            account_number="2087008012",
            bank_name="United Bank for Africa",
            bank_code="000004",
            transaction_id="txn-1",
        )

    assert result.account_name == "John Doe"
    assert result.account_status == "Active"
    assert post.call_args.kwargs["json"]["transactionId"] == "txn-1"
    assert post.call_args.kwargs["json"]["bankName"] == "United Bank for Africa"


@override_settings(**UBA_SETTINGS)
def test_validate_account_generates_transaction_id():
    with (
        patch("aurora.core.services.uba.UBAClient.get_access_token", return_value="Bearer x"),
        patch("aurora.core.services.uba.requests.post", return_value=response(json_data=VALIDATION_RESPONSE)) as post,
        patch("aurora.core.services.uba.UBAClient._new_transaction_id", return_value="generated") as new_transaction_id,
    ):
        UBAClient().validate_account(account_number="2087008012", bank_name="United Bank for Africa")

    new_transaction_id.assert_called_once()
    assert post.call_args.kwargs["json"]["transactionId"] == "generated"


@override_settings(**UBA_SETTINGS)
@pytest.mark.parametrize(
    ("side_effect", "error"),
    [
        (MissingSchema, UBAConfigError),
        (ReadTimeout, UBATransportError),
        (RequestsConnectionError, UBATransportError),
    ],
)
def test_validate_account_transport_errors(side_effect, error):
    with (
        patch("aurora.core.services.uba.UBAClient.get_access_token", return_value="Bearer x"),
        patch("aurora.core.services.uba.requests.post", side_effect=side_effect),
        pytest.raises(error),
    ):
        UBAClient().validate_account(account_number="2087008012", bank_name="United Bank for Africa")


@override_settings(**UBA_SETTINGS)
def test_validate_account_http_error():
    with (
        patch("aurora.core.services.uba.UBAClient.get_access_token", return_value="Bearer x"),
        patch("aurora.core.services.uba.requests.post", return_value=response(status=500)),
        pytest.raises(UBAAPIError) as exc,
    ):
        UBAClient().validate_account(account_number="2087008012", bank_name="United Bank for Africa")

    assert exc.value.code == "500"
    assert exc.value.message == "HTTP 500"


@override_settings(**UBA_SETTINGS)
def test_validate_account_invalid_json():
    with (
        patch("aurora.core.services.uba.UBAClient.get_access_token", return_value="Bearer x"),
        patch("aurora.core.services.uba.requests.post", return_value=response(json_error=ValueError)),
        pytest.raises(UBAAPIError, match="Invalid response from UBA server"),
    ):
        UBAClient().validate_account(account_number="2087008012", bank_name="United Bank for Africa")


@override_settings(**UBA_SETTINGS)
def test_validate_account_rejected():
    payload = {"response": {"responseCode": "4", "accountOperStatus": "Account not valid"}}

    with (
        patch("aurora.core.services.uba.UBAClient.get_access_token", return_value="Bearer x"),
        patch("aurora.core.services.uba.requests.post", return_value=response(json_data=payload)),
        pytest.raises(UBAAPIError) as exc,
    ):
        UBAClient().validate_account(account_number="2087008012", bank_name="United Bank for Africa")

    assert exc.value.code == "4"
    assert exc.value.message == "Account not valid"
