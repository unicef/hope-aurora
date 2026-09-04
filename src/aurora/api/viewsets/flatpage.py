from typing import TYPE_CHECKING, Sequence

from django.contrib.flatpages.models import FlatPage

from ..serializers.flatpage import FlatPageSerializer
from .base import SmartViewSet, StaffOnlyPermission

if TYPE_CHECKING:
    from rest_framework.permissions import _SupportsHasPermission


class FlatPageViewSet(SmartViewSet):
    queryset = FlatPage.objects.all()
    serializer_class = FlatPageSerializer

    def get_permissions(self) -> "Sequence[_SupportsHasPermission]":
        if self.action in ("list", "retrieve"):
            return [StaffOnlyPermission()]
        return super().get_permissions()
