from django.apps import AppConfig


class Config(AppConfig):
    name = "aurora.i18n"

    def ready(self):
        from . import handlers  # noqa
