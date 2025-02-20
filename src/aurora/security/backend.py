from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.utils import timezone

from ..core.models import Organization, Project
from .models import AuroraRole


class AuroraAuthBackend(ModelBackend):
    def has_perm(self, user_obj, perm, obj=None):
        from aurora.registration.models import Registration

        if obj and obj._meta.app_label in ["core", "registration"]:
            if isinstance(obj, Organization):
                qs = AuroraRole.objects.filter(organization=obj)
            elif isinstance(obj, Project):
                qs = AuroraRole.objects.filter(project=obj)
            elif isinstance(obj, Registration):
                qs = AuroraRole.objects.filter(registration=obj)
            else:
                raise ValueError("{obj} must be one instance of Organization|Project|Registration|")
            app_label, perm_name = perm.split(".")
            return (
                qs.filter(
                    user=user_obj,
                    role__permissions__codename=perm_name,
                    role__permissions__content_type__app_label=app_label,
                )
                .filter(valid_from__lte=timezone.now())
                .filter(Q(valid_until__gte=timezone.now()) | Q(valid_until__isnull=True))
                .exists()
            )

        return user_obj.is_active and super().has_perm(user_obj, perm, obj=obj)
