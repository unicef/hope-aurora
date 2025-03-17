from concurrency.fields import AutoIncVersionField
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db import models
from django.db.models import JSONField
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from natural_keys import NaturalKeyModel

from aurora.core.models import Organization, Project
from aurora.registration.models import Registration

User = get_user_model()


class UserProfile(models.Model):
    version = AutoIncVersionField()
    last_update_date = models.DateTimeField(auto_now=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    ad_uuid = models.CharField(max_length=64, unique=True, null=True, blank=True, editable=False)
    custom_fields = JSONField(default=dict, blank=True)
    job_title = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.user}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class AuroraRoleManager(models.Manager):
    def get_by_natural_key(self, org_slug, prj_slug, registration_slug, username, group):
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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

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

    def __str__(self):
        return f"{self.user} -> {self.role} in {self.project}/{self.organization}"

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.registration:
            self.project = self.registration.project
            self.organization = self.project.organization
        elif self.project:
            self.organization = self.project.organization
        return super().save(force_insert, force_update, using, update_fields)

    def natural_key(self):
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


class AuroraUser(User):
    class Meta:
        proxy = True
        verbose_name = _("user")
        verbose_name_plural = _("users")


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
