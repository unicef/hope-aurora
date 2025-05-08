from typing import Any

from django.apps import AppConfig
from django.core import checks

from aurora.security.microsoft_graph import MicrosoftGraphAPI


@checks.register("config")
def check_azure_credentials(app_configs: AppConfig, **kwargs: Any) -> "list[checks.CheckMessage]":
    errors = []

    try:
        api = MicrosoftGraphAPI()
        api.get_token()
    except Exception as e:
        errors.append(checks.Warning("Microsoft Graph API not available", hint=str(e)))
    return errors
