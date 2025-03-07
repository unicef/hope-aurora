from django.core.cache import caches
from django.db.models.signals import post_delete, post_save
from django.utils import timezone

from .models import Message

cache = caches["default"]


def update_cache(sender, instance, **kwargs):
    tznow = timezone.now()
    msconds = tznow.microsecond // 1000
    serial = f"{tznow:%d-%m-%Y:%H:%M:%S}.{msconds:03d}"
    cache.set("i18n", serial)


post_save.connect(update_cache, sender=Message, dispatch_uid="update_message_version")
post_delete.connect(update_cache, sender=Message, dispatch_uid="update_message_version")
