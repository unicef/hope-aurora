from collections.abc import Iterator

from django.contrib.staticfiles import finders
from django.core.files.storage import Storage

# DRF's assets (including Bootstrap 3.4.1) are only used by the browsable API, which is disabled outside DEBUG.
# Leaving them out of list() keeps them out of collectstatic, while find() still serves them in development.
EXCLUDED = ["rest_framework/*"]


class AppDirectoriesFinder(finders.AppDirectoriesFinder):
    def list(self, ignore_patterns: list[str] | None) -> Iterator[tuple[str, Storage]]:
        return super().list([*(ignore_patterns or []), *EXCLUDED])
