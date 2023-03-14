from rest_framework import serializers
from strategy_field.utils import fqn

from aurora.core.models import FlexForm


class FormSerializer(serializers.ModelSerializer):
    base_type = serializers.CharField()
    fields = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name="flexformfield-detail")

    class Meta:
        model = FlexForm
        exclude = ()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["base_type"] = fqn(instance.base_type)
        return data
