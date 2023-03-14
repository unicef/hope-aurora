from admin_extra_buttons.decorators import button
from admin_sync.mixin import SyncMixin as SyncMixin_
from admin_sync.utils import wraps
from django.contrib.admin import action
from django.shortcuts import render


class SyncMixin(SyncMixin_):
    actions = ["publish_action"]

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

    # @choice(order=900, change_list=False)
    # def admin_sync(self, button):
    #     button.choices = [
    #         self._admin_sync_inspect,
    #         self._sync,
    #         self._publish,
    #     ]
    #     return button
    #
    # @view(change_form=True)
    # def _admin_sync_inspect(self, request, pk):
    #     return self.admin_sync_inspect.func(self, request, pk)
    #
    # @view(change_form=True)
    # def _sync(self, request, pk):
    #     return self.sync.func(self, request, pk)
    #
    # @view(change_form=True)
    # def _publish(self, request, pk):
    #     return self.publish.func(self, request, pk)
    #
    # def get_changeform_buttons(self, context):
    #     ignored = ["admin_sync_inspect", "sync", "publish"]
    #     return [
    #         h for h in self.extra_button_handlers.values() if h.change_form in [True, None] and h.name not in ignored
    #     ]
