from django.utils.functional import cached_property
from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.reverse import reverse
from rest_framework.utils.serializer_helpers import BindingDict
from strategy_field.utils import fqn

from ...core.fields import LabelOnlyField
from ...core.utils import build_dict
from ...registration.models import Record


class RecordSerializer(serializers.ModelSerializer):
    registration_url = serializers.SerializerMethodField()
    registrar = serializers.CharField()

    class Meta:
        model = Record
        exclude = ("storage", "files")

    def get_registration_url(self, obj):
        req = self.context["request"]
        return req.build_absolute_uri(reverse("api:registration-detail", kwargs={"pk": obj.registration_id}))


class DataTableRecordSerializer(serializers.ModelSerializer):
    def __init__(self, instance=None, data=empty, **kwargs):
        self.metadata = kwargs.pop("metadata")
        super().__init__(instance, data, **kwargs)

    class Meta:
        model = Record
        fields = ("id", "timestamp", "remote_ip")
        datatables_always_serialize = (
            "id",
            "fields",
        )

    @cached_property
    def fields(self):
        """
        A dictionary of {field_name: field_instance}.
        """
        # `fields` is evaluated lazily. We do this to ensure that we don't
        # have issues importing modules that use ModelSerializers as fields,
        # even if Django's app-loading stage has not yet run.
        fields = BindingDict(self)
        for key, value in self.get_fields().items():
            fields[key] = value
        for field_name, field_defs in self.metadata["base"]["fields"].items():
            if field_defs["type"] not in [fqn(LabelOnlyField)]:
                fields[field_name] = serializers.CharField(read_only=True, source=f"fields.{field_name}", default="N/A")
        fields["flatten"] = serializers.SerializerMethodField(read_only=True, default="N/A")
        return fields

    def get_flatten(self, obj):
        return build_dict(obj)
