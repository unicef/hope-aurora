from django_filters import rest_framework as filters
from rest_framework.decorators import action
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response

from ...registration.models import Record
from ..serializers import RecordSerializer
from .base import SmartViewSet


class RecordFilter(filters.FilterSet):
    id = filters.NumberFilter(field_name="id", lookup_expr="gte")
    after = filters.DateFilter(field_name="timestamp", lookup_expr="gte")

    class Meta:
        model = Record
        fields = ["registration", "after", "id"]


class RecordPaginator(CursorPagination):
    page_size = 10
    ordering = "-id"


class RecordViewSet(SmartViewSet):
    queryset = Record.objects.all()
    serializer_class = RecordSerializer
    filterset_class = RecordFilter
    pagination_class = RecordPaginator

    @action(detail=False)
    def metadata(self, request, pk=None):
        latest = Record.objects.latest("id")
        return Response(
            {
                "id": latest.id,
                "timestamp": latest.timestamp,
                "registration": latest.registration_id,
            }
        )

    # class Meta:
    #     datatables_extra_json = ("fields", )
    #
    #
    # def get_fields(self):
    #     return "fields", {
    #         "artist": [{'label': obj.name, 'value': obj.pk} for obj in Artist.objects.all()],
    #         "genre": [{'label': obj.name, 'value': obj.pk} for obj in Genre.objects.all()]
    #     }
