from typing import TYPE_CHECKING

from django.apps import AppConfig
from django.urls import NoReverseMatch, get_script_prefix, reverse
from django.utils.encoding import iri_to_uri
from smart_admin.decorators import smart_register

if TYPE_CHECKING:
    from django.contrib.flatpages.models import FlatPage


def get_absolute_url(self: "FlatPage") -> str | None:
    from .views import flatpage

    for url in (self.url.lstrip("/"), self.url):
        try:
            return reverse(flatpage, kwargs={"url": url})
        except NoReverseMatch:
            pass
    # Handle script prefix manually because we bypass reverse()
    return iri_to_uri(get_script_prefix().rstrip("/") + self.url)


class Config(AppConfig):
    default = False
    name = "django.contrib.flatpages"

    def ready(self) -> None:
        super().ready()
        from django.contrib.flatpages.models import FlatPage

        from .admin import FlatPageAdmin

        smart_register(FlatPage)(FlatPageAdmin)

        FlatPage.get_absolute_url = get_absolute_url
