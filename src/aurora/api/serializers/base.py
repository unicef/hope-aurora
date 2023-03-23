from rest_framework import serializers


class AuroraHyperlinkedModelSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField()
