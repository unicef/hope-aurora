from rest_framework import serializers
from rest_framework.reverse import reverse

from ...core.models import Organization


class OrganizationSerializer(serializers.HyperlinkedModelSerializer):
    projects = serializers.SerializerMethodField()
    parent = serializers.CharField(source="parent.slug", read_only=True, default=None)

    class Meta:
        model = Organization
        exclude = ("lft", "rght", "tree_id", "level")

    def get_projects(self, obj):
        req = self.context["request"]
        return req.build_absolute_uri(reverse("api:organization-projects", kwargs={"pk": obj.pk}))
