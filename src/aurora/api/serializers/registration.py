from typing import Mapping

from rest_framework import serializers
from rest_framework.fields import Field
from rest_framework.reverse import reverse
from rest_framework.utils.model_meta import FieldInfo

from ...registration.models import Registration


class RegistrationDetailSerializer(serializers.HyperlinkedModelSerializer):
    project = serializers.HyperlinkedRelatedField(
        many=False,  # type: ignore[var-annotated]
        read_only=True,
        view_name="project-detail",
    )
    records = serializers.SerializerMethodField()
    metadata = serializers.SerializerMethodField()

    class Meta:
        model = Registration
        exclude = ("public_key", "handler")

    def get_default_field_names(self, declared_fields: Mapping[str, Field], model_info: FieldInfo) -> list[str]:
        return (
            [model_info.pk.name] + list(declared_fields) + list(model_info.fields) + list(model_info.forward_relations)
        )

    def get_records(self, obj: Registration) -> str:
        req = self.context["request"]
        return req.build_absolute_uri(reverse("api:registration-records", kwargs={"pk": obj.pk}))

    def get_metadata(self, obj: Registration) -> str:
        req = self.context["request"]
        return req.build_absolute_uri(reverse("api:registration-metadata", kwargs={"pk": obj.pk}))


class RegistrationListSerializer(RegistrationDetailSerializer):
    pass
