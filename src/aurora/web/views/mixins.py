from typing import Any

from django.conf import settings
from django.forms import Media
from django.forms.widgets import Script
from django.views import View
from django.views.generic.base import ContextMixin

import aurora
from aurora.core.version_media import VersionMedia


class MediaMixin(ContextMixin, View):
    def get_context_data(self, **kwargs) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["media"] = self.media
        return ctx

    @property
    def media(self) -> Media:
        extra = "" if settings.DEBUG else ".min"
        js_files = [
            "admin/js/vendor/jquery/jquery%s.js" % extra,
            "admin/js/jquery.init.js",
            "jquery.compat%s.js" % extra,
            "js/sentry-5-30%s.js" % extra,
            Script("sentry%s.js" % extra, id="script-sentry", dsn=settings.SENTRY_DSN, version=aurora.VERSION),
            "js/js.cookie%s.js" % extra,
            "js/dark_mode%s.js" % extra,
        ]
        if self.request.user.is_staff:
            js_files.extend(
                [
                    "i18n/i18n_edit%s.js" % extra,
                    "core/js/edit%s.js" % extra,
                ]
            )

        return VersionMedia(js=js_files)
