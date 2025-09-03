from django.apps import AppConfig
from django.core import checks

from .checks import check_azure_credentials


class Config(AppConfig):
    name = "aurora"
    default = True

    def ready(self) -> None:
        checks.register(check_azure_credentials, "aaa")
