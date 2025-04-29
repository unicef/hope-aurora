from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django.http import HttpRequest


def masker(key: str, value: str, config: Any, request: "HttpRequest") -> Any:
    from django_sysinfo.utils import cleanse_setting

    from aurora.core.utils import is_root

    if is_root(request):
        return value
    return cleanse_setting(key, value, config, request)


SYSINFO = {
    "host": True,
    "os": True,
    "python": True,
    "modules": True,
    "masker": "aurora.config.settings.masker",
    "masked_environment": "API|TOKEN|KEY|SECRET|PASS|SIGNATURE|AUTH|_ID|SID|DATABASE_URL",
}
