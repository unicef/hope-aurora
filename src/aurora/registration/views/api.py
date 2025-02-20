from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic.list import ListView

from admin_extra_buttons.utils import handle_basic_auth

from aurora.core.utils import JSONEncoder
from aurora.registration.models import Record, Registration


class RegistrationDataApi(ListView):
    model = Record

    def get(self, request, *args, **kwargs):
        try:
            handle_basic_auth(request)
        except PermissionDenied:
            return HttpResponse(status=401)
        return super().get(request, *args, **kwargs)

    def render_to_response(self, context, **response_kwargs):
        reg = get_object_or_404(Registration, id=self.kwargs["pk"])
        start = int(self.kwargs["start"])
        end = int(self.kwargs["end"])

        data = list(
            reg.record_set.filter(id__gte=start, id__lte=end).values(
                "id", "remote_ip", "timestamp", "files", "fields", "storage"
            )[:1000]
        )
        return JsonResponse(
            {"reg": reg.pk, "start": start, "end": end, "data": data},
            encoder=JSONEncoder,
        )
