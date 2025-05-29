import logging
from typing import TYPE_CHECKING, Any, Mapping, TypeAlias

from constance import config
from django.core.files.uploadedfile import UploadedFile
from django.forms import TextInput, Textarea, Widget

from django.utils.datastructures import MultiValueDict


if TYPE_CHECKING:
    _DataT: TypeAlias = Mapping[str, Any]  # noqa: PYI047

    _FilesT: TypeAlias = MultiValueDict[str, UploadedFile]  # noqa: PYI047

logger = logging.getLogger(__name__)


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
