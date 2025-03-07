import logging

from django.apps import AppConfig
from django.db import OperationalError, ProgrammingError

logger = logging.getLogger(__name__)


class Config(AppConfig):
    name = "aurora.core"

    def ready(self):
        from aurora.core.models import CustomFieldType
        from aurora.core.registry import field_registry

        from . import flags  # noqa
        from .handlers import cache_handler

        cache_handler()
        try:
            for field in CustomFieldType.objects.all():
                try:
                    cls = field.get_class()
                    field_registry.register(cls)
                except Exception as e:
                    logger.exception(e)

        except (OperationalError, ProgrammingError):  # pragma: no-cover
            pass
