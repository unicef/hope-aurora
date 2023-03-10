import logging
from django.conf import settings

from django.contrib.staticfiles.storage import ManifestStaticFilesStorage

logger = logging.getLogger(__name__)


class ForgivingManifestStaticFilesStorage(ManifestStaticFilesStorage):
    def stored_name(self, name: str) -> str:
        try:
            return super().stored_name(name)
        except ValueError as e:
            if settings.DEBUG:
                logger.exception(e)
            return ""

    def hashed_name(self, name, content=None, filename=None) -> str:
        try:
            result = super().hashed_name(name, content, filename)
        except ValueError:
            # When the file is missing, let's forgive and ignore that.
            result = name
        return result
