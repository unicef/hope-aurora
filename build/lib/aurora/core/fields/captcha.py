import secrets

from django import forms

from aurora.core.fields.widgets.captcha import CaptchaWidget

NUMBERS = "0123456789"
TYPES = ["bw", "wb"]
ORIENTATION = "lr"


def get_image_for_number(n: int):
    return f"{n}{secrets.choice(TYPES)}{secrets.choice(ORIENTATION)}.jpg"


def get_random_numbers():
    return secrets.randbelow(100), secrets.randbelow(100)


class CaptchaField(forms.CharField):
    widget = CaptchaWidget
