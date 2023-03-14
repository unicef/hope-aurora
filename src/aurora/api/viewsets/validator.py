from django.http import HttpResponse
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

from aurora.core.models import Validator

from ..serializers.validator import ValidatorSerializer
from .base import SmartViewSet


class ValidatorViewSet(SmartViewSet):
    queryset = Validator.objects.all()
    serializer_class = ValidatorSerializer
    WRAPPER = """
;function {name}(value){{
    return eval('{code}');
}};
"""

    @action(detail=True, permission_classes=[AllowAny], authentication_classes=[SessionAuthentication])
    def validator(self, request, pk):
        obj = self.get_object()
        return HttpResponse(
            self.WRAPPER.format(name=obj.name, code=obj.code.replace("\n", "").replace("\r", "")),
            content_type="application/javascript",
        )

    @action(detail=True, permission_classes=[AllowAny], authentication_classes=[SessionAuthentication])
    def script(self, request, pk):
        obj = self.get_object()
        return HttpResponse(
            obj.code,
            content_type="application/javascript",
        )
