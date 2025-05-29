import time
from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.cache import get_conditional_response
from django.utils.decorators import method_decorator
from django.utils.translation import get_language
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.generic.list import BaseListView

from aurora.core.models import OptionSet
from aurora.core.utils import get_etag
from aurora.state import state


def filter_optionset(obj: OptionSet, pk: str, term: str, lang: str, parent: str | None = None) -> dict[str, Any]:
    def _filter(record: dict[str, Any]) -> bool:
        valid = True
        if pk:
            valid = valid and record["pk"].lower() == pk.lower()
        if term:
            valid = valid and record["label"].lower().startswith(term.lower())
        if parent:
            valid = valid and str(record["parent"]) == str(parent)
        return valid

    return {
        "results": [
            {
                "id": record["pk"],
                "parent": record["parent"],
                "text": record["label"],
            }
            for record in obj.as_json(lang)
            if _filter(record)
        ],
    }


@method_decorator(never_cache, name="dispatch")
class OptionsListVersion(View):
    def get(self, request: "HttpRequest", *args: Any, **kwargs: Any) -> HttpResponse:
        name = self.kwargs["name"]
        obj: OptionSet = get_object_or_404(OptionSet, name=name)
        return JsonResponse(
            {"version": obj.version, "url": reverse("optionset-versioned", args=[obj.name, obj.version])}
        )


class OptionsListView(BaseListView):
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        name = self.kwargs["name"]

        lang = get_language()
        term = request.GET.get("q")
        parent = request.GET.get("parent", self.kwargs.get("parent", None))
        pk = request.GET.get("pk")

        obj: OptionSet = get_object_or_404(OptionSet, name=name)

        if state.collect_messages:
            etag = get_etag(request, time.time())
        else:
            etag = get_etag(
                request,
                obj.pk,
                obj.version,
                lang,
                term,
                parent,
                pk,
            )
        response = get_conditional_response(request, str(etag))
        if response is None:
            data = filter_optionset(obj, pk, term, lang, parent)
            response = JsonResponse(data)
            response["Cache-Control"] = "public, max-age=315360000"
            response["ETag"] = etag
        return response


def service_worker(request: "HttpRequest") -> "HttpResponse":
    return HttpResponse(
        open(settings.PWA_SERVICE_WORKER_PATH).read(),
        content_type="application/javascript",
    )
