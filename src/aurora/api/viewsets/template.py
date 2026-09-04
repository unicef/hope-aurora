from typing import TYPE_CHECKING, Sequence

from rest_framework import serializers

from dbtemplates.models import Template

from .base import SmartViewSet, StaffOnlyPermission

if TYPE_CHECKING:
    from rest_framework.permissions import _SupportsHasPermission


class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        exclude = ()


class TemplateViewSet(SmartViewSet):
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer

    def get_permissions(self) -> "Sequence[_SupportsHasPermission]":
        if self.action in ("list", "retrieve"):
            return [StaffOnlyPermission()]
        return super().get_permissions()
