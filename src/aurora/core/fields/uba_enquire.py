from django import forms
from django.core.exceptions import ValidationError
from django.forms import MultiWidget

from aurora.core.fields.mixins import ConfigurableSmartField, MultiValueWidgetMixin
from aurora.core.services.uba import (
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


class UBANameEnquiryMultiWidget(UBAMultiWidgetMixin, MultiValueWidgetMixin, MultiWidget):
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
        return list(value.values()) if value else [None, None, None, None, None]


class UBANameEnquiryField(ConfigurableSmartField, forms.MultiValueField):
    widget = UBANameEnquiryMultiWidget

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
        values.insert(0, dict(BANKS_CHOICE)[values[0]])
        values.append(self._ignore_error())
        return dict(zip(["name", "uba_code", "number", "holder_name", "ignore_error"], values, strict=True))

    def _ignore_error(self) -> bool:
        flex_field = getattr(self, "flex_field", None)
        if flex_field is None:
            return False
        return flex_field.advanced.get("ignore_error", False)

    def validate(self, value):
        super().validate(value)

        try:
            _, bank_code, account_number, account_full_name, _ = value.values()
        except ValueError:
            raise ValidationError("ValueError: not enough values to unpack") from None

        try:
            result = UBAClient().name_enquiry(bank_code=bank_code, account_number=account_number)
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

        if result.customer_name.lower().strip() != account_full_name.lower().strip():
            raise ValidationError(
                f"Account holder name does not match: ({result.customer_name})",
                code="name_mismatch",
                params={"name": result.customer_name},
            )
