from concurrency.fields import AutoIncVersionField
from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from natural_keys import NaturalKeyModel

from aurora.core.models import Organization
from aurora.registration.models import Registration


class AuroraUser(AbstractUser):
    version = AutoIncVersionField()
    last_update_date = models.DateTimeField(auto_now=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    groups = models.ManyToManyField(
        Group,
        verbose_name=_("groups"),
        blank=True,
        help_text=_(
            "The groups this user belongs to. A user will get all permissions " "granted to each of their groups."
        ),
        related_name="+",
        related_query_name="+",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_("user permissions"),
        blank=True,
        help_text=_("Specific permissions for this user."),
        related_name="+",
        related_query_name="+",
    )

    def save(self, *args, **kwargs):
        if settings.AUTH_USER_MODEL != "security.AuroraUser":
            for attr in [
                "id",
                "username",
                "email",
                "password",
                "first_name",
                "last_name",
                "is_staff",
                "is_active",
                "is_superuser",
            ]:
                setattr(self, attr, getattr(self.user, attr))
        super().save(*args, **kwargs)


class RegistrationRoleManager(models.Manager):
    def get_by_natural_key(self, registration_slug, username, group):
        return self.get(registration__slug=registration_slug, user__username=username, role__name=group)


class RegistrationRole(NaturalKeyModel, models.Model):
    version = AutoIncVersionField()
    last_update_date = models.DateTimeField(auto_now=True)
    registration = models.ForeignKey(Registration, related_name="roles", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.ForeignKey(Group, on_delete=models.CASCADE)
    valid_from = models.DateField(default=timezone.now)
    valid_until = models.DateField(default=None, null=True, blank=True)

    objects = RegistrationRoleManager()

    class Meta:
        unique_together = (("registration", "user", "role"),)

    def natural_key(self):
        return (self.registration.slug, self.user.username, self.role.name)


class OrganizationRoleManager(models.Manager):
    def get_by_natural_key(self, organization_slug, username, group):
        return self.get(organization__slug=organization_slug, user__username=username, role__name=group)


class OrganizationRole(NaturalKeyModel, models.Model):
    version = AutoIncVersionField()
    last_update_date = models.DateTimeField(auto_now=True)
    organization = models.ForeignKey(Organization, related_name="users", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.ForeignKey(Group, on_delete=models.CASCADE)
    valid_from = models.DateField(default=timezone.now)
    valid_until = models.DateField(default=None, null=True)

    objects = OrganizationRoleManager()

    class Meta:
        unique_together = (("organization", "user", "role"),)

    def natural_key(self):
        return (self.organization.slug, self.user.username, self.role.name)
