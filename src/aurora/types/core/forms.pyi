from typing import Protocol

from aurora.core.models import FlexFormField

class SmartProtocol(Protocol):
    flex_field: "FlexFormField"
    smart_attrs: dict
