from django.apps import AppConfig


class Config(AppConfig):
    name = "aurora.security"

    def ready(self):
        from . import handlers  # noqa
