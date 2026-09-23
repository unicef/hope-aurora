from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.db.models import Q
from django.utils import timezone

from aurora.security.models import AuroraRole

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser

    from aurora.security.models import User


@dataclass(frozen=True)
class RoleScope:
    """Where a user is entitled to act, as opposed to what they are entitled to do."""

    organizations: frozenset[int]
    projects: frozenset[int]
    registrations: frozenset[int]
    unlimited: bool

    def as_q(self, organization: str, project: str | None, registration: str | None) -> Q:
        """Build a filter for a model, given its lookup path to each level of the hierarchy."""
        query = Q(**{f"{organization}__in": self.organizations})
        if project:
            query |= Q(**{f"{project}__in": self.projects})
        if registration:
            query |= Q(**{f"{registration}__in": self.registrations})
        return query


UNLIMITED = RoleScope(frozenset(), frozenset(), frozenset(), unlimited=True)


def get_role_scope(user: "User|AnonymousUser") -> RoleScope:
    """Resolve the hierarchy a user's currently valid roles place them in.

    Scope is deliberately independent of which permissions those roles carry: callers are expected
    to have already established *what* the user may do, and need this only to establish *where*.
    A role with no organization, project or registration attached is an explicit grant over
    everything, which is how global access is provisioned.
    """
    if not user.is_authenticated:
        return RoleScope(frozenset(), frozenset(), frozenset(), unlimited=False)
    if user.is_superuser:
        return UNLIMITED

    now = timezone.now()
    rows = (
        AuroraRole.objects.filter(user=user, valid_from__lte=now)
        .filter(Q(valid_until__gte=now) | Q(valid_until__isnull=True))
        .values_list("organization_id", "project_id", "registration_id")
    )

    organizations: set[int] = set()
    projects: set[int] = set()
    registrations: set[int] = set()
    unlimited = False
    # AuroraRole.save() copies a registration's project and organization onto the row, so the
    # coarser columns are context rather than grants of their own: only the narrowest level counts.
    # Reading it this way also survives bulk_create(), which skips that denormalisation entirely.
    for organization, project, registration in rows:
        if registration is not None:
            registrations.add(registration)
        elif project is not None:
            projects.add(project)
        elif organization is not None:
            organizations.add(organization)
        else:
            unlimited = True

    return RoleScope(frozenset(organizations), frozenset(projects), frozenset(registrations), unlimited)
