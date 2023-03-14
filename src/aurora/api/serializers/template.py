from rest_framework import serializers

from dbtemplates.models import Template


class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        exclude = ()
