from typing import TYPE_CHECKING, Iterable

from admin_sync.collector import ForeignKeysCollector
from admin_sync.exceptions import SyncError
from admin_sync.protocol import LoadDumpProtocol

if TYPE_CHECKING:
    from admin_sync.types import Collectable
    from django.db.models import ForeignObjectRel, Model, QuerySet

    from aurora.core.models import Organization


class AuroraSyncProjectProtocol(LoadDumpProtocol):
    pass
    # def collect(self, data: "Collectable", collect_related: bool = True) -> "Iterable[Model]":
    #     from aurora.core.models import Project
    #
    #     if len(data) == 0:
    #         raise SyncError("Empty queryset")  # pragma: no cover
    #
    #     if not isinstance(data[0], Project):  # pragma: no cover
    #         raise ValueError("AuroraSyncProjectProtocol can be used only for Project")
    #     return_value = []
    #     for o in list(data):
    #         c = ForeignKeysCollector(False)
    #         c.collect([o])
    #         return_value.extend(c.data)
    #     return return_value


class OrgForeignKeysCollector(ForeignKeysCollector):
    # def collect(self, objs: "Collectable", collect_related: bool = None) -> None:
    #     return super().collect(objs, collect_related)

    def get_related_for_field(self, obj: "Organization", field: "ForeignObjectRel") -> "Iterable[Model]":  # type: ignore[override]
        if field.name == "parent":
            if obj not in self._visited:
                return [obj.parent]
            return []
        return super().get_related_for_field(obj, field)


class AuroraSyncOrganizationProtocol(LoadDumpProtocol):
    collector_class = OrgForeignKeysCollector
