from typing import TYPE_CHECKING, Sequence

from django.http import HttpRequest, HttpResponse
from rest_framework.decorators import action

from aurora.core.models import Validator

from ..serializers.validator import ValidatorSerializer
from .base import SmartViewSet, StaffOnlyPermission

if TYPE_CHECKING:
    from rest_framework.permissions import _SupportsHasPermission


class ValidatorViewSet(SmartViewSet):
    queryset = Validator.objects.all()
    serializer_class = ValidatorSerializer
    WRAPPER = """
;function {name}(value){{
    return eval('{code}');
}};
"""

    def get_permissions(self) -> "Sequence[_SupportsHasPermission]":
        if self.action in ("list", "retrieve", "validator", "script"):
            return [StaffOnlyPermission()]
        return super().get_permissions()

    @action(detail=True)
    def validator(self, request: HttpRequest, pk: str) -> HttpResponse:
        obj = self.get_object()
        return HttpResponse(
            self.WRAPPER.format(name=obj.name, code=obj.code.replace("\n", "").replace("\r", "")),
            content_type="application/javascript",
        )

    @action(detail=True)
    def script(self, request: HttpRequest, pk: str) -> HttpResponse:
        obj = self.get_object()
        return HttpResponse(
            obj.code,
            content_type="application/javascript",
        )
