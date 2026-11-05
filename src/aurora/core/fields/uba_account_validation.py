from dataclasses import dataclass

from django import forms
from django.core.exceptions import ValidationError
from django.forms import MultiWidget

from aurora.core.fields.mixins import ConfigurableSmartField, MultiValueWidgetMixin
from aurora.core.services.uba import (
    AccountValidationResult,
    UBAAccountNotFound,
    UBAAuthError,
    UBAConfigError,
    UBAClient,
    UBAAPIError,
    UBATransportError,
)

from .uba_common import (
    BANKS_CHOICE,
    BANKS_SORTED_CHOICES,
    AccountHolderNameUBATextInput,
    AccountNumberUBATextInput,
    UBAMultiWidgetMixin,
    UBASelect,
)

SUCCESS_RESPONSE_CODE = "00"
VALID_ACCOUNT_STATUSES = ("Active",)
VALID_ACCOUNT_OPER_STATUSES = ("Name Enquiry successful",)


def _normalize(value: object) -> str:
    return str(value or "").strip().casefold()


@dataclass(frozen=True)
class AccountValidationRule:
    """A response field and the values it is allowed to have."""

    attribute: str
    allowed_values: tuple[str, ...]
    advanced_key: str
    error_code: str
    label: str

    def allowed(self, advanced: dict) -> set[str]:
        values = advanced.get(self.advanced_key)
        if values is None:
            values = self.allowed_values
        elif isinstance(values, str):
            values = (values,)
        return {_normalize(value) for value in values}

    def check(self, result: AccountValidationResult, advanced: dict) -> None:
        value = getattr(result, self.attribute, None)
        if _normalize(value) not in self.allowed(advanced):
            raise ValidationError(
                f"{self.label}: {value}",
                code=self.error_code,
                params={self.attribute: value},
            )


# Add a new AccountValidationRule here to validate another response field.
ACCOUNT_VALIDATION_RULES = (
    AccountValidationRule(
        attribute="response_code",
        allowed_values=(SUCCESS_RESPONSE_CODE,),
        advanced_key="response_code_values",
        error_code="uba_invalid_response_code",
        label="Invalid response code",
    ),
    AccountValidationRule(
        attribute="account_status",
        allowed_values=VALID_ACCOUNT_STATUSES,
        advanced_key="account_status_values",
        error_code="uba_invalid_account_status",
        label="Invalid account status",
    ),
    AccountValidationRule(
        attribute="oper_status",
        allowed_values=VALID_ACCOUNT_OPER_STATUSES,
        advanced_key="account_oper_status_values",
        error_code="uba_invalid_account_oper_status",
        label="Invalid account operating status",
    ),
)


class UBAAccountValidationMultiWidget(UBAMultiWidgetMixin, MultiValueWidgetMixin, MultiWidget):
    template_name = "django/forms/widgets/uba.html"
    custom_render = True

    def __init__(self, optionset_name=None, attrs=None):
        attrs = dict() if attrs is None else attrs
        attrs["optionset_name"] = optionset_name
        widgets = (
            UBASelect(attrs),
            AccountNumberUBATextInput(attrs),
            AccountHolderNameUBATextInput(attrs),
        )
        super().__init__(widgets, attrs)

    def decompress(self, value):
        return list(value.values()) if value else [None, None, None]


class UBAAccountValidationField(ConfigurableSmartField, forms.MultiValueField):
    widget = UBAAccountValidationMultiWidget
    validation_rules = ACCOUNT_VALIDATION_RULES

    def __init__(self, *args, **kwargs):
        fields = [
            forms.ChoiceField(choices=BANKS_SORTED_CHOICES),
            forms.CharField(),
            forms.CharField(),
        ]
        kwargs["template_name"] = "django/forms/uba.html"
        if hasattr(self, "flex_field"):
            optionset_name = self.flex_field.advanced.get("optionset_name", None)
            kwargs["widget"] = self.widget(optionset_name=optionset_name)
        super().__init__(fields, *args, **kwargs)

    def compress(self, values):
        bank_code = values[0] if values else ""
        return {
            "name": dict(BANKS_CHOICE).get(bank_code, bank_code),
            "uba_code": bank_code,
            "number": values[1] if len(values) > 1 else "",
            "holder_name": values[2] if len(values) > 2 else "",
            "account_name": "",
            "account_status": "",
            "ignore_error": self._ignore_error(),
        }

    def _advanced(self) -> dict:
        flex_field = getattr(self, "flex_field", None)
        return flex_field.advanced if flex_field is not None else {}

    def _ignore_error(self) -> bool:
        return self._advanced().get("ignore_error", False)

    def _validate_response(self, result: AccountValidationResult) -> None:
        advanced = self._advanced()
        for rule in self.validation_rules:
            rule.check(result, advanced)

    def validate(self, value):
        super().validate(value)

        try:
            bank_code = value["uba_code"]
            account_number = value["number"]
            bank_name = value["name"]
            account_full_name = value["holder_name"]
        except (KeyError, TypeError):
            raise ValidationError("ValueError: not enough values to unpack") from None

        try:
            result = UBAClient().validate_account(
                account_number=account_number,
                bank_name=bank_name,
                bank_code=bank_code,
            )
        except UBAAccountNotFound as e:
            raise ValidationError("Invalid account number") from e
        except UBAConfigError as e:
            raise ValidationError("Invalid UBA Api url") from e
        except (UBAAuthError, UBATransportError) as e:
            if self._ignore_error():
                return
            raise ValidationError("Cannot reach UBA server", code="uba_error") from e
        except UBAAPIError as e:
            raise ValidationError(f"{e.message}: (error {e.code})") from e

        if _normalize(result.account_name) != _normalize(account_full_name):
            raise ValidationError(
                f"Account holder name does not match: ({result.account_name})",
                code="name_mismatch",
                params={"name": result.account_name},
            )

        self._validate_response(result)

        value["account_name"] = result.account_name
        value["account_status"] = result.account_status
