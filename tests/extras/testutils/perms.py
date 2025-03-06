from contextlib import ContextDecorator
from random import choice

from django.contrib.auth.models import Permission
from faker import Faker

from aurora.core.models import Organization
from aurora.registration.models import Project, Registration
from aurora.security.models import AuroraRole

from .factories import GroupFactory

whitespace = " \t\n\r\v\f"
lowercase = "abcdefghijklmnopqrstuvwxyz"
uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
letters = lowercase + uppercase
ascii_lowercase = lowercase
ascii_uppercase = uppercase
ascii_letters = ascii_lowercase + ascii_uppercase

faker = Faker()


def text(length, choices=ascii_letters):
    """returns a random (fixed length) string

    :param length: string length
    :param choices: string containing all the chars can be used to build the string

    .. seealso::
       :py:func:`rtext`
    """
    return "".join(choice(choices) for x in range(length))


def get_group(name=None, permissions=None):
    group = GroupFactory(name=(name or text(5)))
    permission_names = permissions or []
    for permission_name in permission_names:
        try:
            app_label, codename = permission_name.split(".")
        except ValueError:
            raise ValueError("Invalid permission name `{0}`".format(permission_name)) from None
        try:
            permission = Permission.objects.get(content_type__app_label=app_label, codename=codename)
        except Permission.DoesNotExist:
            raise Permission.DoesNotExist("Permission `{0}` does not exists", permission_name) from None

        group.permissions.add(permission)
    return group


class user_grant_permissions(ContextDecorator):  # noqa
    caches = [
        "_group_perm_cache",
        "_user_perm_cache",
        "_dsspermissionchecker",
        "_officepermissionchecker",
        "_perm_cache",
        "_dss_acl_cache",
    ]

    def __init__(self, user, permissions=None, target: "Registration|Project|Organization" = None):
        self.user = user
        if not isinstance(permissions, (list, tuple)):
            permissions = [permissions]
        self.permissions = permissions
        self.group = None
        if target:
            self.target = target
            if isinstance(target, Organization):
                self.kwargs = {"organization": self.target}
            elif isinstance(target, Project):
                self.kwargs = {
                    "project": self.target,
                    "organization": self.target.organization,
                }
            elif isinstance(target, Registration):
                self.kwargs = {
                    "project": target.project,
                    "registration": self.target,
                    "organization": target.project.organization,
                }
            else:
                raise ValueError("target must one instance of Registration|Project|Organization")

    def __enter__(self):
        for cache in self.caches:
            if hasattr(self.user, cache):
                delattr(self.user, cache)
        self.group = get_group(permissions=self.permissions or [])
        self.user.groups.add(self.group)
        if self.target:
            AuroraRole.objects.get_or_create(user=self.user, role=self.group, **self.kwargs)

    def __exit__(self, e_typ, e_val, trcbak):
        if self.group:
            self.user.groups.remove(self.group)
            self.group.delete()

        if e_typ:
            raise e_typ(e_val).with_traceback(trcbak)

    def start(self):
        """Activate a patch, returning any created mock."""
        return self.__enter__()

    def stop(self):
        """Stop an active patch."""
        return self.__exit__(None, None, None)
