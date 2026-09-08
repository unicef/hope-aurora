from typing import TYPE_CHECKING

from django.db.models import QuerySet

from aurora.core.models import FlexForm

from ..serializers.form import FormSerializer
from .base import LastModifiedFilter, SmartViewSet

if TYPE_CHECKING:
    from aurora.security.models import User


class FlexFormFilter(LastModifiedFilter):
    class Meta:
        model = FlexForm
        fields = ("modified_after", "project")


class FlexFormViewSet(SmartViewSet):
    queryset = FlexForm.objects.all()
    serializer_class = FormSerializer
    filterset_class = FlexFormFilter

    def scope_queryset(self, qs: QuerySet[FlexForm], user: "User") -> QuerySet[FlexForm]:
        return qs.filter(project_id__in=user.accessible_project_ids)
