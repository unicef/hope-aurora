from django.apps import AppConfig


class Config(AppConfig):
    name = "aurora"
    default = True

    def ready(self) -> None:
        pass
