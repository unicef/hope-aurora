from django.contrib.flatpages.models import FlatPage

from ..serializers.flatpage import FlatPageSerializer
from .base import SmartViewSet


class FlatPageViewSet(SmartViewSet):
    queryset = FlatPage.objects.all()
    serializer_class = FlatPageSerializer
