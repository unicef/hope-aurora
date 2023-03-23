import os
from collections import OrderedDict

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

from ...core.utils import get_etag, get_session_id
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

    @action(detail=True, permission_classes=[AllowAny])
    def version(self, request, pk=None):
        reg: Registration = self.get_object()
        return Response(
            {
                "version": reg.version,
                "url": reg.get_absolute_url(),
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
