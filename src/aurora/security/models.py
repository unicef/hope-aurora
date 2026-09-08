from typing import Iterable

from concurrency.fields import AutoIncVersionField
from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.db.models import JSONField, Q
from django.db.models.base import ModelBase
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from natural_keys import NaturalKeyModel
from unicef_security.models import SecurityMixin

from aurora.core.models import Organization, Project
from aurora.registration.models import Registration


def _active_roles(user: "User") -> "models.QuerySet[AuroraRole]":
    """QuerySet of the user's currently valid AuroraRole assignments."""
    now = timezone.now()
    return (
        AuroraRole.objects.filter(user=user)
        .filter(valid_from__lte=now)
        .filter(Q(valid_until__gte=now) | Q(valid_until__isnull=True))
    )


class User(SecurityMixin, AbstractUser):
    class Meta(AbstractUser.Meta):
        swappable = "AUTH_USER_MODEL"
        ordering = ("username",)

    def has_active_role(self) -> bool:
        """Return True if the user has at least one currently valid role assignment."""
        return _active_roles(self).exists()

    @property
    def accessible_organization_ids(self) -> list[int]:
        """PKs of organizations the user is authorized for via active roles.

        ``AuroraRole.save`` derives the organization for project- and
        registration-scoped roles, so every active role contributes here.
        """
        if self.is_superuser:
            return list(Organization.objects.values_list("pk", flat=True))
        return list(
            _active_roles(self)
            .exclude(organization_id__isnull=True)
            .values_list("organization_id", flat=True)
            .distinct()
        )

    @property
    def accessible_project_ids(self) -> list[int]:
        """PKs of projects the user is authorized for via active roles.

        Covers project- and registration-scoped roles; ``AuroraRole.save``
        derives the project for registration-scoped roles.
        """
        if self.is_superuser:
            return list(Project.objects.values_list("pk", flat=True))
        return list(
            _active_roles(self).exclude(project_id__isnull=True).values_list("project_id", flat=True).distinct()
        )

    @property
    def accessible_registration_ids(self) -> list[int]:
        """PKs of registrations the user is authorized for via active roles.

        Only registration-scoped roles grant access to a registration.
        """
        if self.is_superuser:
            return list(Registration.objects.values_list("pk", flat=True))
        return list(
            _active_roles(self)
            .exclude(registration_id__isnull=True)
            .values_list("registration_id", flat=True)
            .distinct()
        )


class UserProfile(models.Model):
    version = AutoIncVersionField()
    last_update_date = models.DateTimeField(auto_now=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    ad_uuid = models.CharField(max_length=64, unique=True, null=True, blank=True, editable=False)
    custom_fields = JSONField(default=dict, blank=True)
    job_title = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return f"{self.user}"

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)


class AuroraRoleManager(models.Manager["AuroraRole"]):
    def get_by_natural_key(
        self, org_slug: str, prj_slug: str, registration_slug: str, username: str, group: str
    ) -> "AuroraRole":
        if org_slug:
            flt = {"organization__slug": org_slug}
        elif prj_slug:
            flt = {"project__slug": prj_slug}
        elif registration_slug:
            flt = {"registration__slug": registration_slug}
        else:
            flt = {}
        return self.get(user__username=username, role__name=group, **flt)


class AuroraRole(NaturalKeyModel, models.Model):
    version = AutoIncVersionField()
    last_update_date = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    organization = models.ForeignKey(
        Organization,
        blank=True,
        null=True,
        related_name="members",
        on_delete=models.CASCADE,
    )
    project = models.ForeignKey(Project, blank=True, null=True, related_name="members", on_delete=models.CASCADE)
    registration = models.ForeignKey(
        Registration,
        blank=True,
        null=True,
        related_name="members",
        on_delete=models.CASCADE,
    )

    role = models.ForeignKey(Group, on_delete=models.CASCADE)
    valid_from = models.DateField(default=timezone.now)
    valid_until = models.DateField(default=None, null=True, blank=True)

    objects = AuroraRoleManager()

    class Meta:
        unique_together = (("organization", "project", "registration", "user", "role"),)
        verbose_name = _("role")
        verbose_name_plural = _("roles")

    def __str__(self) -> str:
        return f"{self.user} -> {self.role} in {self.project}/{self.organization}"

    def save(
        self,
        force_insert: bool | tuple[ModelBase, ...] = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
    ) -> None:
        if self.registration:
            self.project = self.registration.project
            self.organization = self.project.organization
        elif self.project:
            self.organization = self.project.organization
        return super().save(
            force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields
        )

    def natural_key(self) -> tuple[str | None, ...]:
        if self.organization:
            return (
                self.organization.slug,
                None,
                None,
                self.user.username,
                self.role.name,
            )
        if self.project:
            return (None, self.project.slug, None, self.user.username, self.role.name)
        if self.registration:
            return (
                None,
                None,
                self.registration.slug,
                self.user.username,
                self.role.name,
            )
        return (None, None, None, self.user.username, self.role.name)


class AuroraGroup(Group):
    class Meta:
        proxy = True
        verbose_name = _("group")
        verbose_name_plural = _("groups")


class AuroraPermission(Permission):
    class Meta:
        proxy = True
        verbose_name = _("permission")
        verbose_name_plural = _("permissions")
