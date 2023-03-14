import adminactions.actions as actions
import debug_toolbar
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path, re_path

from aurora.core.views import service_worker
from aurora.web.views.site import error_404

actions.add_to_site(admin.site)

handler404 = error_404

urlpatterns = [
    path(settings.DJANGO_ADMIN_URL, admin.site.urls),
    re_path(r"sax-\d*/", admin.site.urls),
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
]

urlpatterns += i18n_patterns(
    path("", include("aurora.registration.urls")),
    path("", include("aurora.core.urls")),
)
