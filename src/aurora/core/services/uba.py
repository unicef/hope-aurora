import logging
import secrets
from dataclasses import dataclass
from typing import Any

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import MissingSchema, ReadTimeout

logger = logging.getLogger(__name__)

TOKEN_CACHE_KEY = "uba-token"  # noqa: S105
SUCCESS_STATUS = "00"
TOKEN_EXPIRY_MARGIN = 30

UBA_STATUS_CODES = {
    "00": "Success",
    "99": "Failed",
    "405": "Method not allowed",
    "400": "Invalid Credentials",
    "500": "ESB Internal Error",
    "111": "Invalid Scheme Type",
    "114": "Invalid Account Number",
    "115": "Requested function not supported",
    "116": "Insufficient funds",
    "119": "Transaction not permitted to card holder",
    "121": "Withdrawal amount limit exceeded",
    "133": "Format error (Sent by Web Service)",
    "134": "Data retrieval error",
    "135": "Country Code is missing",
    "136": "Invalid data type",
    "137": "Configuration error! Unable to retrieve bank details",
    "138": "Configuration error! Unable to retrieve SOL details",
    "139": "Unknown error Check the service logs",
    "140": "Security violation",
    "141": "Security violation",
    "142": "Invalid fee amount/account",
    "143": "Invalid Stan",
    "145": "Invalid processing code",
    "163": "Invalid Cheque Status",
    "166": "Permission not granted",
    "180": "Transfer Limit Exceeded",
    "181": "Cheques are in different books",
    "182": "Not all Cheques could be stopped",
    "183": "Cheque not issued to this account",
    "184": "Account closed",
    "185": "Invalid currency",
    "186": "Block does not exist",
    "187": "Cheque stopped",
    "188": "Invalid Rate Currency Combination",
    "189": "Cheque Book Already Issued",
    "190": "DD Already Paid",
    "800": "Network message was accepted",
    "902": "Invalid transaction/ function code",
    "904": "Format Error (Any format related errors etc)",
    "906": "Cut-over in progress",
    "907": "CBA Inoperative",
    "909": "System malfunction",
    "911": "Service timed out, status is unknown",
    "913": "Duplicate STAN",
    "01": "Status unknown, please wait for settlement report",
    "03": "Invalid Sender",
    "05": "Do not honor",
    "06": "Dormant Account",
    "07": "Invalid Account",
    "08": "Account Name Mismatch",
    "09": "Request processing in progress",
    "12": "Invalid transaction",
    "13": "Invalid Amount",
    "14": "Invalid Batch Number",
    "15": "Invalid Session or Record ID",
    "16": "Unknown Bank Code",
    "17": "Invalid Channel",
    "18": "Wrong Method Call",
    "21": "No action taken",
    "25": "Unable to locate record",
    "26": "Duplicate record",
    "30": "Format error",
    "34": "Suspected fraud",
    "35": "Contact sending bank",
    "51": "No sufficient funds",
    "57": "Transaction not permitted to sender",
    "58": "Transaction not permitted on channel",
    "61": "Transfer limit Exceeded",
    "63": "Security violation",
    "65": "Exceeds withdrawal frequency",
    "68": "Response received too late",
    "69": "Unsuccessful Account/Amount block",
    "70": "Unsuccessful Account/Amount unblock",
    "71": "Empty Mandate Reference Number",
    "91": "Beneficiary Bank not available",
    "92": "Routing error",
    "94": "Duplicate transaction",
    "96": "System malfunction",
    "97": "Timeout waiting for response from destination",
}


def status_message(code: str | None, default: str = "Unknown error") -> str:
    if code is None:
        return default
    return UBA_STATUS_CODES.get(str(code), default)


def join_url(base_url: str, endpoint: str) -> str:
    """Join the UBA base URL with an endpoint, preserving any base path."""
    if not base_url:
        return endpoint
    return f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"


class UBAError(Exception):
    pass


class UBAConfigError(UBAError):
    pass


class UBATransportError(UBAError):
    pass


class UBAAuthError(UBAError):
    pass


class UBAAPIError(UBAError):
    def __init__(self, message: str, *, code: str | None = None, payload: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = None if code is None else str(code)
        self.payload = payload or {}


class UBAAccountNotFoundError(UBAAPIError):
    pass


@dataclass(frozen=True)
class UBAConfig:
    token_url: str
    name_enquiry_url: str
    account_validation_url: str
    appl_code: str
    client_no: str
    x_auth_cred: str
    consumer_key: str
    consumer_secret: str
    timeout: int = 60

    @classmethod
    def from_settings(cls) -> "UBAConfig":
        base_url = settings.UBA_BASE_URL
        return cls(
            token_url=settings.UBA_TOKEN_URL,
            name_enquiry_url=join_url(base_url, settings.UBA_NAME_ENQUIRY_URL),
            account_validation_url=join_url(base_url, settings.UBA_ACCOUNT_VALIDATION_URL),
            appl_code=settings.UBA_APPL_CODE,
            client_no=settings.UBA_CLIENT_NO,
            x_auth_cred=settings.UBA_X_AUTH_CRED,
            consumer_key=settings.UBA_CONSUMER_KEY,
            consumer_secret=settings.UBA_CONSUMER_SECRET,
        )


@dataclass(frozen=True)
class NameEnquiryResult:
    customer_name: str
    status_code: str
    raw: dict[str, Any]


@dataclass(frozen=True)
class AccountValidationResult:
    transaction_id: str
    account_name: str
    account_number: str
    bank_code: str
    account_status: str
    oper_status: str
    raw: dict[str, Any]
    session_id: str | None = None
    response_code: str | None = None
    bank_verification_number: str | None = None
    kyc_level: str | None = None

    @classmethod
    def from_response(
        cls,
        data: dict[str, Any],
        *,
        fallback_account_number: str = "",
        fallback_bank_code: str = "",
    ) -> "AccountValidationResult":
        response = data.get("response", data)
        code = response.get("responseCode")
        oper_status = response.get("accountOperStatus") or ""
        account_name = response.get("accountName") or ""
        success = (code is None or str(code) == SUCCESS_STATUS) and (
            bool(account_name) or "success" in oper_status.lower()
        )
        if not success:
            message = status_message(code, default=oper_status or "Account validation failed")
            raise UBAAPIError(message, code=code, payload=data)
        return cls(
            transaction_id=response.get("transactionId", ""),
            account_name=account_name,
            account_number=response.get("accountNumber") or fallback_account_number,
            bank_code=response.get("bankCode") or fallback_bank_code,
            account_status=response.get("accountStatus") or "",
            oper_status=oper_status,
            raw=data,
            session_id=response.get("sessionID"),
            response_code=None if code is None else str(code),
            bank_verification_number=response.get("bankVerificationNumber"),
            kyc_level=response.get("kycLevel"),
        )


class UBAClient:
    """Single entry point for every UBA Open Banking call."""

    def __init__(self, config: UBAConfig | None = None) -> None:
        self._config = config

    @property
    def config(self) -> UBAConfig:
        return self._config or UBAConfig.from_settings()

    def get_access_token(self, *, force: bool = False) -> str:
        token = cache.get(TOKEN_CACHE_KEY)
        if token and not force:
            return token

        for _ in range(2):
            try:
                response = requests.post(
                    self.config.token_url,
                    data={"grant_type": "client_credentials"},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    auth=HTTPBasicAuth(self.config.consumer_key, self.config.consumer_secret),
                    timeout=self.config.timeout,
                )
            except MissingSchema as e:
                raise UBAConfigError("Invalid UBA Api url") from e
            except (ReadTimeout, RequestsConnectionError):
                continue

            if response.status_code != 200:
                continue

            try:
                data = response.json()
                token = f"{data['token_type']} {data['access_token']}"
                expires_in = data.get("expires_in")
            except (KeyError, TypeError, ValueError):
                continue

            timeout = max(1, int(expires_in) - TOKEN_EXPIRY_MARGIN) if expires_in else None
            cache.set(TOKEN_CACHE_KEY, token, timeout=timeout)
            return token

        raise UBAAuthError("Cannot get UBA token")

    def _headers(self, *, access_code: str | None = None, checksum: str | None = None) -> dict[str, str]:
        headers = {
            "AccessCode": access_code or self.get_access_token(),
            "Applcode": self.config.appl_code,
            "Clientno": self.config.client_no,
            "X-Auth-Cred": self.config.x_auth_cred,
        }
        if checksum:
            headers["Checksum"] = checksum
        return headers

    def name_enquiry(
        self,
        *,
        bank_code: str,
        account_number: str,
        country_code: str = "NG",
    ) -> NameEnquiryResult:
        force_token_refresh = False

        for _ in range(2):
            try:
                access_code = self.get_access_token(force=force_token_refresh)
            except UBAAuthError:
                force_token_refresh = True
                continue

            payload = {
                "receiverBankCode": bank_code,
                "receiverAccountNumber": account_number,
                "countryCode": country_code,
                "tranType": "nameenquiry",
            }
            try:
                response = requests.post(
                    self.config.name_enquiry_url,
                    headers=self._headers(access_code=access_code),
                    json=payload,
                    timeout=self.config.timeout,
                )
            except MissingSchema as e:
                raise UBAConfigError("Invalid UBA Api url") from e
            except (ReadTimeout, RequestsConnectionError):
                force_token_refresh = True
                continue

            if response.status_code != 200:
                force_token_refresh = True
                continue

            data = response.json()
            if data.get("errorFlag") == "false" and str(data.get("statusCode")) == "0":
                return NameEnquiryResult(
                    customer_name=data.get("customerName", ""),
                    status_code=str(data.get("statusCode")),
                    raw=data,
                )

            code = data.get("statusCode") or data.get("errCode")
            message = data.get("statusMsg") or data.get("errDesc") or status_message(code)
            if str(code) == "4":
                raise UBAAccountNotFoundError("Invalid account number", code=code, payload=data)
            raise UBAAPIError(str(message), code=code, payload=data)

        raise UBATransportError("Cannot reach UBA server")

    def validate_account(  # noqa: PLR0913
        self,
        *,
        account_number: str,
        bank_name: str,
        bank_code: str = "",
        country_code: str = "NGA",
        currency_code: str = "NGN",
        channel_code: str = "1",
        account_type: str = "Retail",
        transaction_id: str | None = None,
    ) -> AccountValidationResult:
        payload = {
            "transactionId": transaction_id or self._new_transaction_id(),
            "accountNumber": account_number,
            "countryCode": country_code,
            "currencyCode": currency_code,
            "channelCode": channel_code,
            "bankCode": bank_code,
            "bankName": bank_name,
            "accountType": account_type,
        }
        try:
            response = requests.post(
                self.config.account_validation_url,
                headers=self._headers(),
                json=payload,
                timeout=self.config.timeout,
            )
        except MissingSchema as e:
            raise UBAConfigError("Invalid UBA Api url") from e
        except (ReadTimeout, RequestsConnectionError) as e:
            raise UBATransportError("Cannot reach UBA server") from e

        if response.status_code != 200:
            raise UBAAPIError(
                f"HTTP {response.status_code}",
                code=str(response.status_code),
                payload={},
            )

        try:
            data = response.json()
        except ValueError as e:
            raise UBAAPIError("Invalid response from UBA server") from e

        return AccountValidationResult.from_response(
            data,
            fallback_account_number=account_number,
            fallback_bank_code=bank_code,
        )

    @staticmethod
    def _new_transaction_id() -> str:
        return timezone.now().strftime("%y%m%d%H%M%S") + str(secrets.randbelow(10))
