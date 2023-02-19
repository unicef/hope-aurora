from rest_framework import serializers
from rest_framework.reverse import reverse

from ...core.models import Project


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    registrations = serializers.SerializerMethodField()

    class Meta:
        model = Project
        exclude = ("lft", "rght", "tree_id", "level")
        # lookup_field = "slug"
        # extra_kwargs = {
        #     'url': {'lookup_field': 'slug'}
        # }

    def get_registrations(self, obj):
        req = self.context["request"]
        return req.build_absolute_uri(reverse("api:project-registrations", kwargs={"pk": obj.pk}))
