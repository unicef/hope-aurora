from adminactions.utils import get_attr
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.utils import timezone

from ..core.models import Organization, Project
from .models import AuroraRole


class AuroraAuthBackend(ModelBackend):
    def has_perm(self, user_obj, perm, obj=None):
        from aurora.registration.models import Registration

        if obj and isinstance(obj, Organization):
            raise NotImplementedError
        elif obj and isinstance(obj, Project):
            raise NotImplementedError
        elif obj and isinstance(obj, Registration):
            app_label, perm_name = perm.split(".")
            org = get_attr(obj, "project.organization")
            return (
                AuroraRole.objects.filter(Q(registration=obj) | Q(organization=org) | Q(project=obj.project))
                .filter(
                    user=user_obj,
                    role__permissions__codename=perm_name,
                    role__permissions__content_type__app_label=app_label,
                )
                .filter(valid_from__lte=timezone.now())
                .filter(Q(valid_until__gte=timezone.now()) | Q(valid_until__isnull=True))
                .exists()
            )

        return user_obj.is_active and super().has_perm(user_obj, perm, obj=obj)


#
# class RegistrationAuthBackend(ModelBackend):
#     def has_perm(self, user_obj, perm, obj=None):
#         from aurora.registration.models import Registration
#
#         if obj and isinstance(obj, Registration):
#             app_label, perm_name = perm.split(".")
#             return (
#                 RegistrationRole.objects.filter(
#                     registration=obj,
#                     user=user_obj,
#                     role__permissions__codename=perm_name,
#                     role__permissions__content_type__app_label=app_label,
#                 )
#                 .filter(valid_from__lte=timezone.now())
#                 .filter(Q(valid_until__gte=timezone.now()) | Q(valid_until__isnull=True))
#                 .exists()
#             )
#
#         return user_obj.is_active and super().has_perm(user_obj, perm, obj=obj)
#
#
# class OrganizationAuthBackend(ModelBackend):
#     def _get_group_permissions(self, user_obj):
#         # user_groups_field = get_user_model()._meta.get_field('organizationrole_set')
#         # user_groups_query = 'group__%s' % user_groups_field.related_query_name()
#         perms = Permission.objects.filter(group__organizationrole__user=user_obj)
#         return perms
#
#     def has_perm(self, user_obj, perm, obj=None):
#         from aurora.registration.models import Registration
#
#         if obj and isinstance(obj, Registration):
#             app_label, perm_name = perm.split(".")
#             return (
#                 OrganizationRole.objects.filter(
#                     user=user_obj,
#                     organization=obj.project.organization,
#                     role__permissions__codename=perm_name,
#                     role__permissions__content_type__app_label=app_label,
#                 )
#                 .filter(valid_from__lte=timezone.now())
#                 .filter(Q(valid_until__gte=timezone.now()) | Q(valid_until__isnull=True))
#                 .exists()
#             )
#
#         return user_obj.is_active and super().has_perm(user_obj, perm, obj=obj)
