import requests
from constance import config
from django import forms
from django.core.exceptions import ValidationError
from django.forms import MultiWidget
from django.forms.widgets import TextInput


# https://documenter.getpostman.com/view/20828158/2s93sW7aEc#4fda8a6a-0c21-42b2-a86b-03dce41303ad
class IMTONameEnquiryMultiWidget(MultiWidget):
    def __init__(self, *args, **kwargs):
        self.widgets = (
            TextInput({"placeholder": "Bank Code"}),
            TextInput({"placeholder": "Account Number"}),
            TextInput({"placeholder": "Account Holder Name"}),
        )
        super().__init__(self.widgets, *args, **kwargs)

    def decompress(self, value):
        return value.rsplit("|") if value else [None, None, None]


class IMTONameEnquiryField(forms.fields.MultiValueField):
    widget = IMTONameEnquiryMultiWidget

    def __init__(self, *args, **kwargs):
        list_fields = [
            forms.fields.CharField(max_length=16),
            forms.fields.CharField(max_length=32),
            forms.fields.CharField(max_length=128),
        ]
        super().__init__(list_fields, *args, **kwargs)

    def compress(self, values):
        return "|".join(values)

    def validate(self, value):
        super().validate(value)
        try:
            account_number, bank_code, account_full_name = value.rsplit("|")
        except ValueError:
            raise ValidationError("ValueError: not enough values to unpack")
        headers = {
            "x-token": config.IMTO_TOKEN,
        }
        body = {"accountNumber": account_number, "bankCode": bank_code}
        try:
            response = requests.post(config.IMTO_NAME_ENQUIRY_URL, headers=headers, json=body, timeout=60)
            if (
                response.status_code == 200
                and not response.json()["error"]
                and response.json()["code"] == "00"
                and (
                    not config.IMTO_ACCOUNT_HOLDER_NAME_CHECK_ENABLED
                    or response.json()["data"]["beneficiaryAccountName"] == account_full_name
                )
            ):
                return
            if response.status_code == 500:
                message = response.reason
            elif response.json()["error"]:
                message = response.json()["error"]
            elif 300 <= response.status_code < 500:
                message = f"Error {response.status_code}"
            elif response.json()["data"]["beneficiaryAccountName"].lower().strip() != account_full_name.lower().strip():
                message = f"Wrong account holder {account_full_name}"
            else:
                message = "Generic Error"
        except ConnectionError:
            message = "Could not connect"
        raise ValidationError(message)
