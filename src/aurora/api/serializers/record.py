from rest_framework import serializers
from rest_framework.reverse import reverse

from ...registration.models import Record


class RecordSerializer(serializers.ModelSerializer):
    registration_url = serializers.SerializerMethodField()
    registrar = serializers.CharField()
    project = serializers.ReadOnlyField(source="registration.project.pk")
    organization = serializers.ReadOnlyField(source="registration.project.organization.pk")
    project_slug = serializers.ReadOnlyField(source="registration.project.slug")
    organization_slug = serializers.ReadOnlyField(source="registration.project.organization.slug")

    class Meta:
        model = Record
        exclude = ("storage", "files")

    def get_registration_url(self, obj: Record) -> str:
        req = self.context["request"]
        return req.build_absolute_uri(reverse("api:registration-detail", kwargs={"pk": obj.registration_id}))
