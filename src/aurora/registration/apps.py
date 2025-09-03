import re
from typing import TYPE_CHECKING, Never

from django.apps import AppConfig
from django.db.models.signals import post_save

if TYPE_CHECKING:
    from dbtemplates.models import Template

rex1 = re.compile(r"registration/(?P<lang>.*)/(?P<name>.*)\.html")
rex2 = re.compile(r"registration/(?P<name>.*)\.html")


class Config(AppConfig):
    name = "aurora.registration"

    def ready(self) -> Never:
        from dbtemplates.models import Template

        post_save.connect(
            on_templates_change,
            sender=Template,
        )


def on_templates_change(instance: "Template", *args, **kwargs) -> Never:
    if instance.name.startswith("registration/"):
        from aurora.registration.models import Registration

        if m := (rex1.match(instance.name) or rex2.match(instance.name)):
            slug = m.group("name")
            if reg := Registration.objects.filter(slug=slug).first():
                reg.save()
