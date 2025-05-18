import logging
from typing import TYPE_CHECKING, Any, Iterable, ClassVar, Protocol

from django.core.serializers import get_serializer

from admin_sync.collector import ForeignKeysCollector
from admin_sync.exceptions import ProtocolError, SyncError
from admin_sync.protocol import LoadDumpProtocol
from django.core.serializers.json import Deserializer as JsonDeserializer
from django.db import connections, transaction
from django.db.models import Model, Q
from django.core.serializers.jsonl import Serializer as JsonLSerializer, Deserializer as JsonLDeserializer

if TYPE_CHECKING:
    from admin_sync.types import Collectable
    from django.core.serializers.base import Serializer, Deserializer

logger = logging.getLogger(__name__)


class AuroraSyncRegistrationProtocol(LoadDumpProtocol):
    # def serialize(self, data: Iterable) -> Any:
    #     data = self.collect(data)
    #     return self.serializer.serialize(data, use_natural_foreign_keys=True, use_natural_primary_keys=True)
    #
    # def deserialize(self, payload: str) -> list[list[Any]]:
    #     processed = []
    #     try:
    #         connection = connections[self.using]
    #         with connection.constraint_checks_disabled(), transaction.atomic(self.using):
    #             objects = self.deserializer_class(payload, ignorenonexistent=True, handle_forward_references=True)
    #             for obj in objects:
    #                 obj.save(using=self.using)
    #                 processed.append([obj.object._meta.object_name, str(obj.object.pk)])
    #     except Exception as e:
    #         logger.exception(e)
    #         raise ProtocolError(e) from None
    #     return processed

    def collect(self, data: "Collectable", collect_related: bool = True) -> "Iterable[Model]":
        from aurora.core.models import FlexFormField, FormSet
        from aurora.registration.models import Registration

        reg: Registration
        if len(data) == 0:
            raise SyncError("Empty queryset")  # pragma: no cover

        if not isinstance(data[0], Registration):  # pragma: no cover
            raise ValueError("AuroraSyncRegistrationProtocol can be used only for Registration")
        return_value = []
        for reg in list(data):
            return_value.extend([reg.project.organization, reg.project])

            c = ForeignKeysCollector(False)
            c.collect([reg.flex_form, reg.validator, reg])
            c.add(reg.scripts.all())

            fs = FormSet.objects.filter(parent=reg.flex_form)
            fs_forms = [f.flex_form for f in fs] + [f.parent for f in fs]
            c.add(fs_forms)

            fields = FlexFormField.objects.filter(Q(flex_form=reg.flex_form) | Q(flex_form__in=fs_forms))
            validators = [f.validator for f in fields]
            validators.extend([f.validator for f in fs])
            c.add(validators)
            c.add(fields)
            c.add(fs)
            return_value.extend(c.data)
        return return_value
