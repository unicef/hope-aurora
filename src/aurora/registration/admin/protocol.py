import logging
from typing import Any, Iterable, Sequence

from admin_sync.collector import ForeignKeysCollector
from admin_sync.exceptions import ProtocolError, SyncError
from admin_sync.protocol import LoadDumpProtocol
from django.core.serializers.json import Deserializer as JsonDeserializer
from django.db import connections, transaction
from django.db.models import Q

logger = logging.getLogger(__name__)


class AuroraSyncRegistrationProtocol(LoadDumpProtocol):
    def serialize(self, data: Iterable):
        return super().serialize(data)

    def deserialize(self, payload: str) -> list[list[Any]]:
        processed = []
        try:
            connection = connections[self.using]
            with connection.constraint_checks_disabled(), transaction.atomic(self.using):
                objects = JsonDeserializer(
                    payload,
                    ignorenonexistent=True,
                    handle_forward_references=True,
                )
                for obj in objects:
                    obj.save(using=self.using)
                    processed.append(
                        [
                            obj.object._meta.object_name,
                            str(obj.object.pk),
                            str(obj.object),
                        ]
                    )
        except Exception as e:
            logger.exception(e)
            raise ProtocolError(e) from None
        return processed

    def collect(self, data: Sequence, collect_related=True):
        from aurora.core.models import FlexFormField, FormSet
        from aurora.registration.models import Registration

        if len(data) == 0:
            raise SyncError("Empty queryset")  # pragma: no cover

        if not isinstance(data[0], Registration):  # pragma: no cover
            raise ValueError("AuroraSyncRegistrationProtocol can be used only for Registration")
        return_value = []
        for reg in list(data):
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
