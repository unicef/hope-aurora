import json
from datetime import datetime
from typing import Dict

from admin_extra_buttons.decorators import button, view
from admin_sync.mixin import SyncMixin as SyncMixin_
from admin_sync.perms import check_publish_permission, check_sync_permission
from admin_sync.utils import SyncResponse, is_local, is_remote, wraps
from django.contrib import messages
from django.contrib.admin import action
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


class SyncMixin(SyncMixin_):
    actions = ["publish_action"]
    UPDATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    @view(
        decorators=[csrf_exempt],
        http_basic_auth=True,
        enabled=is_remote,
        permission=check_sync_permission,
    )
    def get_version(self, request, key):
        obj = self.model.objects.get_by_natural_key(*key.split("|"))
        return SyncResponse(
            {"version": obj.version, "last_update_date": obj.last_update_date.strftime(self.UPDATE_FORMAT)}
        )

    def get_remote_version(self, request, pk):
        obj = self.get_object(request, pk)
        payload = self.get_remote_data(request, "get_version", obj)
        return json.loads(payload)

    @button(visible=is_local, order=999, permission=check_sync_permission)
    def check_remote_version(self, request, pk):
        obj = self.get_object(request, pk)
        v = self.get_remote_version(request, pk)
        remote_date = datetime.strptime(v["last_update_date"], self.UPDATE_FORMAT)
        local_date = datetime.strptime(obj.last_update_date.strftime(self.UPDATE_FORMAT), self.UPDATE_FORMAT)
        if remote_date > local_date:
            self.message_user(
                request, f"Remote Record is most recent than the local one: {remote_date}", messages.WARNING
            )
        else:
            self.message_user(
                request,
                f"Remote last update {remote_date} ({v['version']})",
            )

    @button(visible=is_local, order=999, permission=check_publish_permission)
    def publish(self, request, pk):
        obj = self.get_object(request, pk)
        i: Dict = self.get_remote_version(request, obj)
        if i["version"] == obj.version:
            return super().publish.func(self, request, pk)
        else:
            self.message_user(request, "Version mismatch. Fetch before publish", messages.ERROR)

    @button(
        visible=lambda b: b.model_admin.admin_sync_show_inspect(),
        html_attrs={"style": "background-color:red"},
    )
    def admin_sync_inspect_multi(self, request):
        context = self.get_common_context(request, title="Sync Inspect")
        collector = self.protocol_class(request)
        data = collector.collect(self.get_queryset(request))
        context["data"] = data
        return render(request, "admin/admin_sync/inspect.html", context)
        # return JsonResponse(c.models, safe=False)

    @action(description="Publish")
    def publish_action(self, request, queryset):
        for r in queryset.all():
            data = self.get_sync_data(request, [self.get_object(request, r.pk)])
            ret = self.post_data_to_remote(request, wraps(data))
            self.message_user(request, f"{ret}")
