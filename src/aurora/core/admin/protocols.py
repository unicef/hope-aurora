from typing import TYPE_CHECKING, Collection, Iterable, final

from admin_sync.collector import ForeignKeysCollector
from admin_sync.exceptions import SyncError
from admin_sync.protocol import LoadDumpProtocol

from aurora.core.models import Organization, Project

if TYPE_CHECKING:
    from admin_sync.types import Collectable
    from django.db.models import ForeignObjectRel, Model


class AuroraSyncProjectProtocol(LoadDumpProtocol):
    def collect(self, data: "Collectable") -> "Collection[Model]":
        from aurora.core.models import Project

        if not data:
            raise SyncError("Empty queryset")  # pragma: no cover

        if isinstance(data, list) and not isinstance(data[0], Project):  # pragma: no cover
            raise ValueError("AuroraSyncProjectProtocol can be used only for Project")
        return_value = []
        for o in list(data):
            c = ForeignKeysCollector(False)
            c.collect([o])
            return_value.extend(c.data)
        return return_value


class OrgForeignKeysCollector(ForeignKeysCollector):
    def collect(self, objs: "Collectable", collect_related: bool = None) -> None:
        return super().collect(objs, collect_related)

    def get_related_for_field(self, obj: "Model", field: "ForeignObjectRel") -> "Iterable[Model]":
        if isinstance(obj, Organization):
            if field.name == "parent":
                if obj not in self._visited:
                    return [obj.parent]
                return []
        return super().get_related_for_field(obj, field)


class AuroraSyncOrganizationProtocol(LoadDumpProtocol):
    collector_class = OrgForeignKeysCollector
