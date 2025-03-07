from rest_framework import serializers
from strategy_field.utils import fqn

from aurora.core.models import FlexFormField


class FlexFormFieldSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True, default=None)

    class Meta:
        model = FlexFormField
        exclude = ()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["field_type"] = fqn(instance.field_type)
        return data
