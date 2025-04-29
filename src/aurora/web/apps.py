import logging
from typing import TYPE_CHECKING

from django.apps import AppConfig
from django.core.cache import cache
from django.db.models.signals import post_save

if TYPE_CHECKING:
    from dbtemplates.models import Template

logger = logging.getLogger(__name__)


def get_key_version(key: str) -> str:
    return cache.get(f"{key}:version")


def incr_key_version(key: str) -> str:
    try:
        cache.incr(f"{key}:version", 1)
    except ValueError:
        cache.set(f"{key}:version", 1)
    return get_key_version(key)


class Config(AppConfig):
    name = "aurora.web"

    def ready(self) -> None:
        from dbtemplates.models import Template

        post_save.connect(invalidate_page_cache, Template, dispatch_uid="template_saved")


def invalidate_page_cache(instance: "Template", **kwargs) -> None:
    try:
        incr_key_version(instance.name)
    except Exception as e:  # pragma: no cover
        logger.exception(e)
