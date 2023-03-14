from ...registration.models import Record
from ..serializers import RecordSerializer
from .base import SmartViewSet


class RecordViewSet(SmartViewSet):
    queryset = Record.objects.all()
    serializer_class = RecordSerializer

    # class Meta:
    #     datatables_extra_json = ("fields", )
    #
    #
    # def get_fields(self):
    #     return "fields", {
    #         "artist": [{'label': obj.name, 'value': obj.pk} for obj in Artist.objects.all()],
    #         "genre": [{'label': obj.name, 'value': obj.pk} for obj in Genre.objects.all()]
    #     }
