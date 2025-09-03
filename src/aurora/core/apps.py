import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class Config(AppConfig):
    name = "aurora.core"

    def ready(self) -> None:
        from . import flags  # noqa
        from .handlers import cache_handler

        cache_handler()
