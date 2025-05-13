from typing import Any, Sequence

from django.apps import AppConfig
from django.core import checks

from aurora.security.microsoft_graph import MicrosoftGraphAPI


def check_azure_credentials(app_configs: Sequence[AppConfig], **kwargs: Any) -> "Sequence[checks.CheckMessage]":
    errors = []

    try:
        api = MicrosoftGraphAPI()
        api.get_token()
    except Exception as e:  # noqa: BLE001
        errors.append(checks.Warning("Microsoft Graph API not available", hint=str(e)))
    return errors
