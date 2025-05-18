import json
import logging
import zlib
from datetime import datetime
from http import HTTPStatus
from json import JSONDecodeError
from typing import Any
from urllib.parse import quote, unquote

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from requests import RequestException
from urllib3.exceptions import NewConnectionError, HTTPError, MaxRetryError, RequestError

from admin_extra_buttons.decorators import button, view
from admin_sync.conf import config

# from admin_sync.exceptions import PublishError, ProtocolError
from admin_sync.mixins import SyncModelAdmin as SyncMixin_

# from admin_sync.utils import SyncResponse, is_local, is_remote, wraps, unwrap
from django.contrib import messages, admin
from django.contrib.admin import action
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from admin_extra_buttons.handlers import BaseExtraHandler
from django.db.models import Model
from django.http import HttpRequest, HttpResponseRedirect, HttpResponse, JsonResponse
from django.utils.translation import gettext as _
from aurora.security.models import User
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)


def credential_holder(request):
    print(111.1, "credential_holder", request.user)


def sync_auth_handler(request: HttpRequest) -> User | AnonymousUser:
    print(111.1, "sync_auth_handler", request.user)
    return request.user


def check_publish_permission(request: HttpRequest, obj: Model, handler: BaseExtraHandler) -> bool:
    return True
    # return handler.model_admin.check_publish_permission(request, obj)


def check_sync_permission(request: HttpRequest, obj: Model, handler: BaseExtraHandler) -> bool:
    return True
    # return handler.model_admin.check_sync_permission(request, obj)


def waf_encode(data: str) -> bytes:
    return zlib.compress(data.encode())


def waf_decode(payload: bytes) -> str:
    return zlib.decompress(payload).decode()


class SyncMixin(SyncMixin_, admin.ModelAdmin):
    actions: tuple[str, ...] = ("publish_action",)
    UPDATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    #
    # @view(  # type: ignore[arg-type]
    #     decorators=[csrf_exempt],
    #     http_auth_handler=sync_auth_handler,
    #     # enabled=is_remote,
    #     permission=check_sync_permission,
    # )
    # def get_version(self, request, key):
    #     try:
    #         obj = self.model.objects.get_by_natural_key(*key.split("|"))
    #         payload = {
    #             "version": obj.version,
    #             "last_update_date": obj.last_update_date.strftime(self.UPDATE_FORMAT),
    #         }
    #     except ObjectDoesNotExist:
    #         payload = {
    #             "version": 0,
    #             "last_update_date": "1900-01-01 00:00:00",
    #         }
    #     return SyncResponse(payload)
    #
    # #
    # def get_remote_version(self, request, pk) -> dict[str, int | str]:
    #     try:
    #         obj = self.get_object(request, pk)
    #         payload = self.get_remote_data(request, "get_version", obj)
    #     except ObjectDoesNotExist:
    #         payload = {"version": 0, "last_update_date": ""}
    #     return json.loads(payload)
    #
    # @button(visible=is_local, order=999, permission=check_sync_permission)  # type: ignore[arg-type]
    # def check_remote_version(self, request, pk):
    #     try:
    #         obj = self.get_object(request, pk)
    #         v = self.get_remote_version(request, pk)
    #         remote_date = datetime.strptime(v["last_update_date"], self.UPDATE_FORMAT)
    #         local_date = datetime.strptime(obj.last_update_date.strftime(self.UPDATE_FORMAT), self.UPDATE_FORMAT)
    #         if remote_date > local_date:
    #             self.message_user(
    #                 request,
    #                 f"Remote Record is most recent than the local one: {remote_date}",
    #                 messages.WARNING,
    #             )
    #         else:
    #             self.message_user(
    #                 request,
    #                 f"Remote last update {remote_date} ({v['version']})",
    #             )
    #     except (HTTPError, ConnectionError) as e:
    #         logger.error(e)
    #         self.message_user(request, "Unable to connect to remote server", messages.ERROR)
    #         return

    # @view(
    #     decorators=[csrf_exempt],
    #     http_auth_handler=sync_auth_handler,
    #     # enabled=is_remote,
    #     permission=check_sync_permission,
    # )
    # def receive(self, request: HttpRequest) -> "HttpResponse":
    #     try:
    #         raw_data = waf_decode(request.body)
    #         payload = self.protocol_class(request).deserialize(raw_data)
    #         return JsonResponse({"status_code": 200, "records": len(payload), "size": len(request.body)})
    #     except (ProtocolError, UnicodeDecodeError) as e:
    #         return JsonResponse({"error": str(e), "status_code": HTTPStatus.BAD_REQUEST}, status=HTTPStatus.BAD_REQUEST)
    #     except JSONDecodeError as e:
    #         return JsonResponse({"error": str(e), "status_code": HTTPStatus.BAD_REQUEST}, status=HTTPStatus.BAD_REQUEST)

    # @button(order=999, permission=check_publish_permission)  # type: ignore[arg-type]
    # def publish(self, request, pk):
    #     try:
    #         context = self.get_common_context(request, pk, title="Publish to REMOTE", server=config.REMOTE_SERVER)
    #         obj = context["original"]
    #         if request.method == "POST":
    #             data = self.protocol_class(request).serialize([obj])
    #             result = self.post_data_to_remote(request, waf_encode(data))
    #             self.message_user(request, f"Published {result}", messages.SUCCESS)
    #         return render(request, "admin/admin_sync/publish.html", context)
    #     except ProtocolError as e:
    #         self.message_user(request, str(e), messages.ERROR)
    #     except PublishError as e:
    #         self.message_user(request, f"Remote Server Error: {e}", messages.ERROR)
    #     except (RequestException, PublishError) as e:
    #         logger.error(e)
    #         self.message_user(request, "Unable to connect to remote server", messages.ERROR)
    #         return

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
