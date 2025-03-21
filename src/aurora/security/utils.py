import secrets
import string

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail


def generate_password(length=20):
    pwd = ""
    count = 0
    length = max(8, length)
    while count < length:
        upper = [secrets.choice(string.ascii_uppercase)]
        lower = [secrets.choice(string.ascii_lowercase)]
        num = [secrets.choice(string.digits)]
        symbol = [secrets.choice(string.punctuation)]
        everything = upper + lower + num + symbol
        pwd += secrets.choice(everything)
        count += 1
    return pwd


def generate_pwd(user_pk):
    subject = "Aurora Credentials"
    pwd = generate_password()
    user = get_user_model().objects.get(pk=user_pk)
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
