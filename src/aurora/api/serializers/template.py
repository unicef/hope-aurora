from dbtemplates.models import Template

from rest_framework import serializers


class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        exclude = ()
