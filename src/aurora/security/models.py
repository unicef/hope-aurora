from concurrency.fields import AutoIncVersionField
from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.db.models import JSONField
from django.utils import timezone
from natural_keys import NaturalKeyModel

from aurora.core.models import Organization
from aurora.registration.models import Registration


class UserProfile(models.Model):
    version = AutoIncVersionField()
    last_update_date = models.DateTimeField(auto_now=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    ad_uuid = models.CharField(max_length=64, unique=True, null=True, blank=True, editable=False)
    custom_fields = JSONField(default=dict, blank=True)
    job_title = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
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
