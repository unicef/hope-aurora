import logging
from typing import TYPE_CHECKING

from django.template import Library

from aurora.i18n.get_text import gettext as _

from ...core.models import FormSet

if TYPE_CHECKING:
    from ..forms import SmartBaseFormSet


logger = logging.getLogger(__name__)
register = Library()


@register.simple_tag()
def formset_config(formset: "SmartBaseFormSet") -> dict[str, str | bool | None]:
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
