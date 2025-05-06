from typing import Any

from ..settings import DEBUG

FLAGS_STATE_LOGGING: bool = DEBUG

FLAGS: dict[str, Any] = {
    "DEVELOP_DEVELOPER": [],
    "DEVELOP_DEBUG_TOOLBAR": [],
    "SENTRY_JAVASCRIPT": [],
    "I18N_COLLECT_MESSAGES": [],
    "IS_ROOT": [],
}
