from typing import TYPE_CHECKING

from django.template import Template, TemplateDoesNotExist, TemplateSyntaxError
from django.template.loaders.base import Loader as BaseLoader

if TYPE_CHECKING:
    from dbtemplates.models import Template as DBTemplate


def get_loaders() -> list[BaseLoader]:
    from django.template.loader import _engine_list

    loaders = []
    for engine in _engine_list():
        loaders.extend(engine.engine.template_loaders)
    return loaders


def get_template_source(name: str) -> Template:
    source = None
    for loader in get_loaders():
        if loader.__module__.startswith("dbtemplates."):
            # Don't give a damn about dbtemplates' own loader.
            continue
        for origin in loader.get_template_sources(name):
            try:
                source = loader.get_contents(origin)
            except (NotImplementedError, TemplateDoesNotExist):
                continue
            if source:
                return source
    return source


def check_template_syntax(template: "DBTemplate") -> tuple[bool, Exception | None]:
    try:
        Template(template.content)
    except TemplateSyntaxError as e:
        return (False, e)
    return (True, None)
