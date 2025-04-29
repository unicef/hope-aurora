import string
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils.crypto import get_random_string

if TYPE_CHECKING:
    from aurora.security.models import User


def generate_password(length: int = 20) -> str:
    allowed_chars = string.ascii_uppercase + string.ascii_lowercase + string.digits + string.punctuation
    return get_random_string(length=length, allowed_chars=allowed_chars)


def generate_pwd(user_pk: str) -> str | None:
    subject = "Aurora Credentials"
    pwd = generate_password()
    user: "User" = get_user_model().objects.get(pk=user_pk)
    user.set_password(pwd)
    user.save()

    message = (
        f"Dear {user.first_name}, \n"
        f"you can login to http://register.unicef.org using {user.email} and {pwd} \n\n"
        f"Regards, \n"
        f"Aurora team"
    )
    recipient_list = [
        user.email,
    ]
    send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list)
    return f"{subject} sent to {user.first_name}!"
