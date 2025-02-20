import logging

from django.template import Library

import markdown as md

from aurora.i18n.get_text import gettext as _

from ...core.models import FormSet

logger = logging.getLogger(__name__)
register = Library()


@register.simple_tag()
def formset_config(formset):
    default = {
        "formCssClass": f"form-container-{formset.prefix}",
        "counterPrefix": "",
        "prefix": formset.prefix,
        "namespace": formset.prefix.replace("-", "_").lower(),
        "deleteContainerClass": f"{formset.fs.name}-delete",
        "addContainerClass": f"{formset.fs.name}-add",
        "addText": "Add Another",
        "addCssClass": "formset-add-button",
        "deleteText": "Remove",
        "deleteCssClass": "formset-delete-button",
        "keepFieldValues": False,
        "original": {},
        "onAdd": None,
        "onRemove": None,
    }
    fs_config = formset.fs.advanced.get("smart", {}).get("widget", FormSet.FORMSET_DEFAULT_ATTRS["smart"]["widget"])
    override = {k: v for k, v in fs_config.items() if v}
    config = {**default, **override}
    for e in ["addText", "deleteText", "counterPrefix"]:
        config[e] = _(config[e])
        config["original"][e] = config[e]
    return config


@register.filter()
def markdown(value):
    if value:
        return md.markdown(value, extensions=["markdown.extensions.fenced_code"])
    return ""


@register.filter(name="md")
def _md(value):
    if value:
        p = md.markdown(value, extensions=["markdown.extensions.fenced_code"])
        return p.replace("<p>", "").replace("</p>", "")
    return ""
