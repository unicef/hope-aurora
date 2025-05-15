import json
import logging
from datetime import datetime
from typing import Any
from urllib.parse import quote, unquote

from django.core.exceptions import ObjectDoesNotExist
from urllib3.exceptions import NewConnectionError, HTTPError, MaxRetryError

from admin_extra_buttons.decorators import button, view
from admin_sync.conf import config
from admin_sync.mixin import SyncMixin as SyncMixin_, GetSingleFromRemoteMixin, PublishMixin
from admin_sync.utils import SyncResponse, is_local, is_remote, wraps, unwrap
from django.contrib import messages, admin
from django.contrib.admin import action
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from admin_extra_buttons.handlers import BaseExtraHandler
from django.db.models import Model
from django.http import HttpRequest, HttpResponseRedirect, HttpResponse
from django.utils.translation import gettext as _
from aurora.security.models import User
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)


def credential_holder(request):
    print(111.1, "credential_holder", request.user)


def sync_auth_handler(request: HttpRequest) -> User:
    print(111.1, "sync_auth_handler", request.user)


def check_publish_permission(request: HttpRequest, obj: Model, handler: BaseExtraHandler) -> bool:
    return True
    # return handler.model_admin.check_publish_permission(request, obj)


def check_sync_permission(request: HttpRequest, obj: Model, handler: BaseExtraHandler) -> bool:
    return True
    # return handler.model_admin.check_sync_permission(request, obj)


def waf_encode(data: str) -> dict[str, str]:
    return {"data": quote(data)}


def waf_decode(payload: str) -> str:
    data = json.loads(payload)
    return unquote(data["data"])


class SyncMixin(PublishMixin, admin.ModelAdmin):
    actions: tuple[str, ...] = ("publish_action",)
    UPDATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    @view(  # type: ignore[arg-type]
        decorators=[csrf_exempt],
        http_auth_handler=sync_auth_handler,
        # enabled=is_remote,
        permission=check_sync_permission,
    )
    def get_version(self, request, key):
        try:
            obj = self.model.objects.get_by_natural_key(*key.split("|"))
            payload = {
                "version": obj.version,
                "last_update_date": obj.last_update_date.strftime(self.UPDATE_FORMAT),
            }
        except ObjectDoesNotExist:
            payload = {
                "version": 0,
                "last_update_date": "1900-01-01 00:00:00",
            }
        return SyncResponse(payload)

    #
    def get_remote_version(self, request, pk) -> dict[str, int | str]:
        try:
            obj = self.get_object(request, pk)
            payload = self.get_remote_data(request, "get_version", obj)
        except ObjectDoesNotExist:
            payload = {"version": 0, "last_update_date": ""}
        return json.loads(payload)

    @button(visible=is_local, order=999, permission=check_sync_permission)  # type: ignore[arg-type]
    def check_remote_version(self, request, pk):
        try:
            obj = self.get_object(request, pk)
            v = self.get_remote_version(request, pk)
            remote_date = datetime.strptime(v["last_update_date"], self.UPDATE_FORMAT)
            local_date = datetime.strptime(obj.last_update_date.strftime(self.UPDATE_FORMAT), self.UPDATE_FORMAT)
            if remote_date > local_date:
                self.message_user(
                    request,
                    f"Remote Record is most recent than the local one: {remote_date}",
                    messages.WARNING,
                )
            else:
                self.message_user(
                    request,
                    f"Remote last update {remote_date} ({v['version']})",
                )
        except (HTTPError, ConnectionError) as e:
            logger.error(e)
            self.message_user(request, "Unable to connect to remote server", messages.ERROR)
            return

    @view(
        decorators=[csrf_exempt],
        http_auth_handler=sync_auth_handler,
        # enabled=is_remote,
        permission=check_sync_permission,
    )
    def receive(self, request: HttpRequest) -> "HttpResponse":
        raw_data = waf_decode(request.body.decode())
        breakpoint()
        payload = self.protocol_class(request).deserialize(raw_data)

    @button(order=999, permission=check_publish_permission)  # type: ignore[arg-type]
    def publish(self, request, pk):
        obj = self.get_object(request, pk)
        try:
            i = self.get_remote_version(request, pk)

            if i["version"] > obj.version:
                self.message_user(request, "Version mismatch. Fetch before publish", messages.ERROR)
                return None
            else:
                context = self.get_common_context(request, pk, title="Publish to REMOTE", server=config.REMOTE_SERVER)
                obj = context["original"]
                if request.method == "POST":
                    data = self.protocol_class(request).serialize([obj])
                    self.post_data_to_remote(request, waf_encode(data))

                    raise Exception(data)

                return render(request, "admin/admin_sync/publish.html", context)
        except (HTTPError, ConnectionError, MaxRetryError) as e:
            logger.error(e)
            self.message_user(request, "Unable to connect to remote server", messages.ERROR)
            return

    # @button(  # type: ignore[arg-type]
    #     visible=lambda b: b.model_admin.admin_sync_show_inspect(),
    #     html_attrs={"style": "background-color:red"},
    # )
    # def admin_sync_inspect_multi(self, request):
    #     context = self.get_common_context(request, title="Sync Inspect")
    #     collector = self.protocol_class(request)
    #     data = collector.collect(self.get_queryset(request))
    #     context["data"] = data
    #     return render(request, "admin/admin_sync/inspect.html", context)

    # @action(description="Publish")
    # def publish_action(self, request, queryset):
    #     for r in queryset.all():
    #         data = self.get_sync_data(request, [self.get_object(request, r.pk)])
    #         ret = self.post_data_to_remote(request, wraps(data))
    #         self.message_user(request, f"{ret}")
    #
    # @button(label=_("fetch"), visible=is_local, order=999, permission=check_sync_permission)
    # def sync(self, request: HttpRequest, pk: str) -> HttpResponse | None:
    #     context = self.get_common_context(request, pk,
    #                                       remote_server = config.REMOTE_SERVER,
    #                                       title="Fetching from REMOTE")
    #     if request.method == "POST":
    #         try:
    #             if not is_logged_to_remote(request):
    #                 raise PermissionError
    #             obj = context["original"]
    #             data = self.get_remote_data(request, "dumpdata_single", obj)
    #             info = self.protocol_class(request).deserialize(data)
    #             context["stdout"] = {"details": info}
    #             admin_sync_data_fetched.send(sender=self, data=data)
    #             self.message_user(request, "Success", messages.SUCCESS)
    #             return render(request, "admin/admin_sync/sync_done.html", context)
    #         except PermissionError:
    #             url = local_reverse(admin_urlname(self.model._meta, "remote_login"))
    #             return HttpResponseRedirect(f"{url}?from={quote_plus(request.path)}")
    #         except Exception as e:
    #             logger.exception(e)
    #             self.message_error_to_user(request, e)
    #     # else:
    #     #     if not is_logged_to_remote(request):
    #     #         url = local_reverse(admin_urlname(self.model._meta, "remote_login"))
    #     #         return HttpResponseRedirect(f"{url}?from={quote_plus(request.path)}")
    #
    #     return render(request, "admin/admin_sync/sync.html", context)
