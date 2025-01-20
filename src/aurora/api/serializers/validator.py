from aurora.api.serializers.base import AuroraHyperlinkedModelSerializer
from aurora.core.models import Validator


class ValidatorSerializer(AuroraHyperlinkedModelSerializer):
    class Meta:
        model = Validator
        exclude = ()
