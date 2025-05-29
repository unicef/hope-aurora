from typing import Mapping, Any

from rest_framework import serializers
from rest_framework.fields import Field
from rest_framework.reverse import reverse
from rest_framework.utils.model_meta import FieldInfo

from ...registration.models import Record, Registration


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


class RegistrationRecordSerializerFields(serializers.ModelSerializer):
    class Meta:
        model = Record
        fields = ("pk", "fields", "remote_ip", "timestamp")


class RegistrationRecordSerializerFiles(serializers.ModelSerializer):
    files = serializers.SerializerMethodField()

    class Meta:
        model = Record
        fields = ("pk", "files")

    def get_files(self, obj: Record) -> dict[str, Any]:
        return obj.attachments


class RegistrationRecordSerializerStorage(serializers.ModelSerializer):
    storage = serializers.SerializerMethodField()

    class Meta:
        model = Record
        fields = ("pk", "storage")

    def get_storage(self, obj: Record) -> str:
        return obj.files.tobytes().decode()  # type: ignore[union-attr]


class RegistrationRecordSerializerFull(serializers.ModelSerializer):
    class Meta:
        model = Record
        fields = ("pk", "data", "remote_ip", "timestamp")
