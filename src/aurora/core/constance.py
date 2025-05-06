import logging
from typing import Any, TypeAlias, Mapping

from constance import config
from django.core.files.uploadedfile import UploadedFile
from django.forms import ChoiceField, HiddenInput, TextInput, Textarea, Widget
from django.template import Context, Template
from django.utils.datastructures import MultiValueDict
from django.utils.safestring import SafeString, mark_safe

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    _DataT: TypeAlias = Mapping[str, Any]  # noqa: PYI047

    _FilesT: TypeAlias = MultiValueDict[str, UploadedFile]  # noqa: PYI047

logger = logging.getLogger(__name__)


class ObfuscatedInput(HiddenInput):
    def render(
        self,
        name: str,
        value: Any,
        attrs: dict[str, str] | None = None,
        renderer: Any | None = None,
    ) -> "SafeString":
        context = self.get_context(name, value, attrs)
        context["value"] = str(value)
        context["label"] = "Set" if value else "Not Set"

        tpl = Template('<input type="hidden" name="{{ widget.name }}" value="{{ value }}">{{ label }}')
        return mark_safe(tpl.render(Context(context)))  # noqa: S308


class WriteOnlyWidget(Widget):
    def format_value(self, value: Any) -> str:
        return super().format_value("***")

    def value_from_datadict(self, data: "_DataT", files: "_FilesT", name: str) -> Any:
        value = data.get(name)
        if value == "***":
            return getattr(config, name)
        return value


class WriteOnlyTextarea(WriteOnlyWidget, Textarea):
    pass


class WriteOnlyInput(WriteOnlyWidget, TextInput):
    pass


class GroupChoiceField(ChoiceField):
    def __init__(self, **kwargs: Any) -> None:
        from django.contrib.auth.models import Group

        ret: list[tuple[str | int, str]] = [(c["name"], c["name"]) for c in Group.objects.values("pk", "name")]
        kwargs["choices"] = ret
        super().__init__(**kwargs)
