from rest_framework import serializers

from aurora.core.models import FormSet

from .base import SmartViewSet


class FormSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormSet
        exclude = ()


class FormSetViewSet(SmartViewSet):
    """Viewset automatically provides `list` and `retrieve` actions."""

    queryset = FormSet.objects.all()
    serializer_class = FormSetSerializer
