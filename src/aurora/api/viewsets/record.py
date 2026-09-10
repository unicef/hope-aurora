from typing import TYPE_CHECKING, cast

from django.db.models import QuerySet
from django.http import HttpRequest
from django_filters import rest_framework as filters
from rest_framework.decorators import action
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response

from ...registration.models import Record
from ..serializers import RecordSerializer
from .base import SmartViewSet

if TYPE_CHECKING:
    from aurora.security.models import User


class RecordFilter(filters.FilterSet):
    id = filters.NumberFilter(field_name="id", lookup_expr="gte")
    after = filters.DateFilter(field_name="timestamp", lookup_expr="gte")

    class Meta:
        model = Record
        fields = [
            "registration",
            "after",
            "id",
            "registration__project",
            "registration__project__organization",
        ]


class RecordPaginator(CursorPagination):
    page_size = 10
    ordering = "-id"


class RecordViewSet(SmartViewSet):
    queryset = Record.objects.all()
    serializer_class = RecordSerializer
    filterset_class = RecordFilter
    pagination_class = RecordPaginator

    def scope_queryset(self, qs: QuerySet[Record], user: "User") -> QuerySet[Record]:
        return qs.filter(registration_id__in=user.viewable_registration_ids)

    @action(detail=True)
    def metadata(self, request: HttpRequest, pk: str | None = None) -> Response:
        qs = self.get_queryset()
        if not qs.exists():
            return Response({})
        latest = cast("Record", qs.latest("id"))
        return Response(
            {
                "id": latest.id,
                "timestamp": latest.timestamp,
                "registration": latest.registration_id,
            }
        )
