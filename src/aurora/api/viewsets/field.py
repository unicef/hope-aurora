from aurora.core.models import FlexFormField

from ..serializers.field import FlexFormFieldSerializer
from .base import LastModifiedFilter, SmartViewSet


class FlexFormFieldFilter(LastModifiedFilter):
    class Meta:
        model = FlexFormField
        fields = ("modified_after", "flex_form")


class FlexFormFieldViewSet(SmartViewSet):
    """
    This viewset automatically provides `list` and `retrieve` actions.
    """

    queryset = FlexFormField.objects.all()
    serializer_class = FlexFormFieldSerializer
    filterset_class = FlexFormFieldFilter
