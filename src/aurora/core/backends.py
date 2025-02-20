from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db import IntegrityError

User = get_user_model()


class AnyUserAuthBackend(ModelBackend):  # pragma: no cover
    # Develop only backend
    def authenticate(self, request, username=None, password=None, **kwargs):
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
