from typing import TYPE_CHECKING, Never, Sequence

from django.http import HttpRequest
from rest_framework import exceptions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from aurora.counters.models import Counter

from .base import SmartViewSet, StaffOnlyPermission

if TYPE_CHECKING:
    from rest_framework.permissions import _SupportsHasPermission


class ScopedRateThrottle2(SimpleRateThrottle):
    rate = "3/day"

    def get_cache_key(self, request: HttpRequest, view: APIView) -> str:
        return request.path


class CounterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Counter
        fields = ()


class CounterViewSet(SmartViewSet):
    queryset = Counter.objects.all()
    serializer_class = CounterSerializer

    def get_permissions(self) -> "Sequence[_SupportsHasPermission]":
        if self.action == "refresh":
            return [StaffOnlyPermission()]
        return super().get_permissions()

    @action(
        detail=False,
        throttle_classes=[ScopedRateThrottle2],
    )
    def refresh(self, request: HttpRequest) -> Response:
        Counter.objects.collect()
        latest = Counter.objects.latest()
        return Response(
            {
                "message": "Done",
                "latest": latest.day,
            }
        )

    def throttled(self, request: HttpRequest, wait: float) -> Never:
        """If request is throttled, determine what kind of exception to raise."""
        latest = Counter.objects.latest()
        detail = "Request was throttled. Data updated to %s." % latest.day
        raise exceptions.Throttled(wait=wait, detail=detail)
