from typing import Any

from rest_framework import serializers
from strategy_field.utils import fqn

from aurora.core.models import FlexForm


class FormSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True, default=None)
    base_type = serializers.CharField()
    fields = serializers.HyperlinkedRelatedField(
        many=True,  # type: ignore[assignment]
        read_only=True,
        view_name="flexformfield-detail",
    )

    class Meta:
        model = FlexForm
        exclude = ()

    def to_representation(self, instance: FlexForm) -> dict[str, Any]:
        data = super().to_representation(instance)
        data["base_type"] = fqn(instance.base_type)
        return data
