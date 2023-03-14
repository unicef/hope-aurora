from rest_framework import serializers
from rest_framework.reverse import reverse

from ...registration.models import Registration


class RegistrationDetailSerializer(serializers.ModelSerializer):
    project = serializers.HyperlinkedRelatedField(many=False, read_only=True, view_name="project-detail")
    records = serializers.SerializerMethodField()

    class Meta:
        model = Registration
        exclude = ("public_key",)

    def get_default_field_names(self, declared_fields, model_info):
        return (
            [model_info.pk.name] + list(declared_fields) + list(model_info.fields) + list(model_info.forward_relations)
        )

    def get_records(self, obj):
        req = self.context["request"]
        return req.build_absolute_uri(reverse("api:registration-records", kwargs={"pk": obj.pk}))


class RegistrationListSerializer(RegistrationDetailSerializer):
    id = serializers.HyperlinkedRelatedField(many=False, read_only=True, view_name="registration-detail")

    class Meta:
        model = Registration
        exclude = ("public_key",)
