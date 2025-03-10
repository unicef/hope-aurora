from pathlib import Path

import debug_toolbar
from adminactions import actions
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from aurora.core.views import service_worker
from aurora.web.views.sites import error_404

actions.add_to_site(admin.site)

handler404 = error_404

favicon = Path(__file__).parent / "../web/static/favicon"

urlpatterns = [
    path(settings.DJANGO_ADMIN_URL, admin.site.urls),
    re_path(r"sax-\d*/", admin.site.urls),
    # favicon just for annoying 404 in tests
    path(
        "favicon.ico",
        serve,
        {"document_root": favicon, "path": "favicon.ico"},
    ),
    path("api/", include("aurora.api.urls", namespace="api")),
    path("", include("aurora.web.urls")),
    path("pages/", include("aurora.flatpages.urls")),
    path("charts/", include("aurora.counters.urls", namespace="charts")),
    path("social/", include("social_django.urls", namespace="social")),
    path("captcha/", include("captcha.urls")),
    path("hijack/", include("hijack.urls")),
    path("mdeditor/", include("mdeditor.urls")),
    path("i18n/", include("aurora.i18n.urls")),
    path("__debug__/", include(debug_toolbar.urls)),
    path(r"serviceworker.js", service_worker, name="serviceworker"),
    path(r"sysinfo/", include("django_sysinfo.urls")),
]

urlpatterns += i18n_patterns(
    path("", include("aurora.registration.urls")),
    path("", include("aurora.core.urls")),
)
