from aurora.core.models import FlexForm

from ..serializers.form import FormSerializer
from .base import LastModifiedFilter, SmartViewSet


class FlexFormFilter(LastModifiedFilter):
    class Meta:
        model = FlexForm
        fields = ("modified_after", "project")


class FlexFormViewSet(SmartViewSet):
    queryset = FlexForm.objects.all()
    serializer_class = FormSerializer
    filterset_class = FlexFormFilter
