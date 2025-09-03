from admin_sync.conf import config
from admin_sync.mixins import SyncModelAdmin
from django.db.models import Model
from django.http import HttpRequest


def is_local(request: HttpRequest) -> bool:  # noqa: ARG001
    return bool(config.REMOTE_SERVER)


def is_remote(request: HttpRequest) -> bool:
    return not is_local(request)


class SyncMixin(SyncModelAdmin):
    actions: tuple[str, ...] = ("publish_action",)
    UPDATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def can_publish(self, request: HttpRequest, pk: str | None = None, obj: Model | None = None) -> bool:
        return super().can_publish(request, pk, obj)

    def can_pull(self, request: HttpRequest, pk: str | None = None, obj: Model | None = None) -> bool:
        return super().can_publish(request, pk, obj)
