from django.apps import AppConfig


class Config(AppConfig):
    name = "aurora.i18n"

    def ready(self) -> None:
        from . import handlers  # noqa
