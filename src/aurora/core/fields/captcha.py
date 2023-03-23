import random

from django import forms

from aurora.core.fields.widgets.captcha import CaptchaWidget

NUMBERS = "0123456789"
TYPES = ["bw", "wb"]
ORIENTATION = "lr"


def get_image_for_number(n: int):
    return f"{n}{random.choice(TYPES)}{random.choice(ORIENTATION)}.jpg"


def get_random_numbers():
    return random.randrange(100), random.randrange(100)


class CaptchaField(forms.CharField):
    widget = CaptchaWidget
    #
    # def __init__(self, **kwargs):
    #     # kwargs["required"] = True
    #     # kwargs["label"] = ""
    #     # kwargs["help_text"] = ""
    #     super().__init__(**kwargs)
    #
    # def widget_attrs(self, widget):
    #     attrs = super().widget_attrs(widget)
    #     op = get_random_numbers()
    #     attrs['data-numbers'] = f"{op[0]}-{op[1]}"
    #     return attrs
