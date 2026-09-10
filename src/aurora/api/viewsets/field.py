from typing import TYPE_CHECKING

from django.db.models import QuerySet

from aurora.core.models import FlexFormField

from ..serializers.field import FlexFormFieldSerializer
from .base import LastModifiedFilter, SmartViewSet

if TYPE_CHECKING:
    from aurora.security.models import User


class FlexFormFieldFilter(LastModifiedFilter):
    class Meta:
        model = FlexFormField
        fields = ("modified_after", "flex_form")


class FlexFormFieldViewSet(SmartViewSet):
    """Viewset automatically provides `list` and `retrieve` actions."""

    queryset = FlexFormField.objects.all()
    serializer_class = FlexFormFieldSerializer
    filterset_class = FlexFormFieldFilter

    def scope_queryset(self, qs: QuerySet[FlexFormField], user: "User") -> QuerySet[FlexFormField]:
        return qs.filter(flex_form__project_id__in=user.accessible_project_ids)
