from typing import TYPE_CHECKING

from django.db.models import QuerySet

from rest_framework import serializers

from aurora.core.models import FormSet

from .base import SmartViewSet

if TYPE_CHECKING:
    from aurora.security.models import User


class FormSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormSet
        exclude = ()


class FormSetViewSet(SmartViewSet):
    """Viewset automatically provides `list` and `retrieve` actions."""

    queryset = FormSet.objects.all()
    serializer_class = FormSetSerializer

    def scope_queryset(self, qs: QuerySet[FormSet], user: "User") -> QuerySet[FormSet]:
        return qs.filter(flex_form__project_id__in=user.accessible_project_ids)
