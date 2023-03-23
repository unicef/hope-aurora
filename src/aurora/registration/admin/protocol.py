from typing import Iterable

from admin_sync.collector import ForeignKeysCollector
from admin_sync.exceptions import SyncError
from admin_sync.protocol import LoadDumpProtocol
from django.db.models import Q


class AuroraSyncRegistrationProtocol(LoadDumpProtocol):
    def collect(self, data: Iterable, collect_related=True):
        from aurora.core.models import FlexFormField, FormSet
        from aurora.registration.models import Registration

        if len(data) == 0:
            raise SyncError("Empty queryset")  # pragma: no cover

        if not isinstance(data[0], Registration):  # pragma: no cover
            raise ValueError("AuroraSyncRegistrationProtocol can be used only for Registration")
        return_value = []
        for reg in list(data):
            # reg: Registration = data[0]
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
