from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.db import IntegrityError

from aurora.security.models import User

if TYPE_CHECKING:
    from django.http import HttpRequest


class AnyUserAuthBackend(ModelBackend):  # pragma: no cover
    def authenticate(
        self, request: "HttpRequest", username: str | None = None, password: str | None = None, **kwargs
    ) -> User | None:
        host = request.get_host()
        if settings.DEBUG and (host.startswith(("localhost", "127.0.0.1"))):
            try:
                if username.startswith("admin"):
                    values = {"is_staff": True, "is_active": True, "is_superuser": True}
                elif username.startswith("user"):
                    values = {"is_staff": False, "is_active": True, "is_superuser": False}
                else:
                    values = {}
                if values:
                    user, __ = User.objects.update_or_create(
                        username=username,
                        defaults={"email": f"{username}@demo.org", **values},
                    )
                    user.set_password(password)
                    user.save()
                    return user
            except (User.DoesNotExist, IntegrityError):
                pass
        return None
