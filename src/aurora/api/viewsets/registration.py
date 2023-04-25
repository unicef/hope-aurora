import csv
import io
import os
from collections import OrderedDict
from urllib import parse

from django.http import HttpResponse, HttpRequest
from django.utils.cache import get_conditional_response
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from ...core.utils import get_etag, get_session_id, build_dict
from ...registration.models import Record, Registration
from ..serializers import RegistrationDetailSerializer, RegistrationListSerializer
from ..serializers.record import DataTableRecordSerializer
from .base import SmartViewSet


class RecordPageNumberPagination(PageNumberPagination):
    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("page", self.request.GET.get("page", 1)),
                    ("count", self.page.paginator.count),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                ]
            )
        )


class RecordFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name="timestamp", lookup_expr="gte")


class RegistrationViewSet(SmartViewSet):
    queryset = Registration.objects.all()

    def get_serializer_class(self):
        if self.detail:
            return RegistrationDetailSerializer
        return RegistrationListSerializer

    def get_permissions(self):
        return [permission() for permission in self.permission_classes]

    # def get_object(self):
    #     queryset = self.filter_queryset(self.get_queryset())
    #     if self.kwargs["attr"].isnumeric():
    #         filter_field = "pk"
    #     else:
    #         filter_field = "slug"
    #     obj = get_object_or_404(queryset, **{filter_field: self.kwargs["attr"]})
    #
    #     # May raise a permission denied
    #     self.check_object_permissions(self.request, obj)
    #
    #     return obj

    @action(detail=True, permission_classes=[AllowAny])
    def metadata(self, request, pk=None):
        reg: Registration = self.get_object()
        return Response(reg.metadata)

    @action(detail=True, permission_classes=[AllowAny], url_path="((?P<language>[a-z-]*)/)*version")
    def version1(self, request, pk, language=""):
        reg: Registration = self.get_object()
        return Response(
            {
                "version": reg.version,
                "url": reg.get_i18n_url(language),
                "auth": request.user.is_authenticated,
                "session_id": get_session_id(request),
                "active": reg.active,
                "protected": reg.protected,
            }
        )

    @action(
        detail=True,
        methods=["GET"],
        renderer_classes=[JSONRenderer],
        pagination_class=RecordPageNumberPagination,
        filter_backends=[DjangoFilterBackend],
    )
    def records(self, request, pk=None):
        obj: Registration = self.get_object()
        if not request.user.has_perm("registration.view_data", obj):
            raise PermissionDenied()
        self.res_etag = get_etag(
            request,
            str(obj.active),
            str(obj.version),
            os.environ.get("BUILD_DATE", ""),
        )
        response = get_conditional_response(request, str(self.res_etag))
        if response is None:
            queryset = (
                Record.objects.defer(
                    "files",
                    "storage",
                )
                .filter(registration=obj)
                .values()
            )
            flt = RecordFilter(request.GET, queryset=queryset)
            if flt.form.is_valid():
                queryset = flt.filter_queryset(queryset)
            page = self.paginate_queryset(queryset)

            if page is None:
                serializer = DataTableRecordSerializer(
                    queryset, many=True, context={"request": request}, metadata=obj.metadata
                )
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                serializer = DataTableRecordSerializer(
                    page, many=True, context={"request": request}, metadata=obj.metadata
                )
                response = self.get_paginated_response(serializer.data)
        response.headers.setdefault("ETag", self.res_etag)
        response.headers.setdefault("Cache-Control", "private, max-age=120")
        return response

    @action(detail=True)
    def csv(self, request: HttpRequest, pk):
        """
        "form": {
            "filters": "({}, {})",
            "include": "['']",
            "exclude": "['']"
        },
        "fmt": {
            "datetime_format": "N j, Y, P",
            "date_format": "N j, Y",
            "time_format": "P"
        },
        "csv": {
            "header": false,
            "doublequote": true,
            "skipinitialspace": true,
            "delimiter": ";",
            "quotechar": "\"",
            "quoting": 0,
            "escapechar": "\\",
            "date_format": "d/m/Y",
            "datetime_format": "N j, Y, P",
            "time_format": "P"
        }
        """
        reg: Registration = self.get_object()
        from aurora.registration.forms import RegistrationExportForm
        from aurora.core.forms import CSVOptionsForm
        from aurora.core.forms import DateFormatsForm

        form = RegistrationExportForm(request.GET, initial=RegistrationExportForm.defaults)
        opts_form = CSVOptionsForm(request.GET, prefix="csv", initial=CSVOptionsForm.defaults)
        fmt_form = DateFormatsForm(request.GET, prefix="fmt", initial=DateFormatsForm.defaults)
        if form.is_valid() and opts_form.is_valid() and fmt_form.is_valid():
            for frm in [form, fmt_form, opts_form]:
                for k, f in frm.defaults.items():
                    if not frm.cleaned_data.get(k):
                        frm.cleaned_data[k] = frm.defaults[k]
            filters, exclude = form.cleaned_data["filters"]
            include_fields = form.cleaned_data["include"]
            exclude_fields = form.cleaned_data["exclude"]
            qs = (
                Record.objects.filter(pk=pk)
                .defer(
                    "storage",
                    "counters",
                    "files",
                )
                .filter(**filters)
                .exclude(**exclude)
                .values("fields", "id", "ignored", "timestamp", "registration_id")
            )
            if qs.count() >= 5000:
                raise Exception("Too many records please change your filters. (max 5000)")
            skipped = []
            all_fields = []
            records = [build_dict(r, **fmt_form.cleaned_data) for r in qs]
            for r in records:
                for field_name in r.keys():
                    if field_name not in skipped and field_name in exclude_fields:
                        skipped.append(field_name)
                    elif field_name not in all_fields and field_name in include_fields:
                        all_fields.append(field_name)
            csv_options = opts_form.cleaned_data
            add_header = csv_options.pop("header")
            date_format = csv_options.pop("date_format")  # noqa
            datetime_format = csv_options.pop("datetime_format")  # noqa
            time_format = csv_options.pop("time_format")  # noqa
            if "download" in request.GET or "preview" in request.GET:
                filename = f"Registration_{reg.slug}.csv"
                if "preview" in request.GET:
                    headers = {}
                else:
                    headers = {"Content-Disposition": 'attachment;filename="%s"' % filename}

                out = io.StringIO()
                writer = csv.DictWriter(
                    out,
                    fieldnames=all_fields,
                    restval="-",
                    extrasaction="ignore",
                    **csv_options,
                )
                if add_header:
                    writer.writeheader()
                writer.writerows(records)
                out.seek(0)
                content = out.read()
                return HttpResponse(
                    content,
                    headers=headers,
                    content_type="text/plain",
                )
            else:

                return Response(
                    {
                        "data": {
                            "download": request.build_absolute_uri(
                                "?download=1&" + parse.urlencode(request.GET.dict(), doseq=False)
                            ),
                            "preview": request.build_absolute_uri(
                                "?preview=1&" + parse.urlencode(request.GET.dict(), doseq=False)
                            ),
                            "count": qs.count(),
                            "filters": filters,
                            "exclude": exclude,
                            "include_fields": [r.pattern for r in include_fields],
                            "fieldnames": all_fields,
                            "skipped": skipped,
                        },
                        "form": {k: str(v) for k, v in form.cleaned_data.items()},
                        "fmt": {k: str(v) for k, v in fmt_form.cleaned_data.items()},
                        "csv": {k: str(v) for k, v in opts_form.cleaned_data.items()},
                    }
                )
        else:
            return Response(
                {
                    "form": form.errors,
                    "fmt": fmt_form.errors,
                    "csv": opts_form.errors,
                }
            )
