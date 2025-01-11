from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import get_language
from django.views.decorators.http import condition
from django.views.i18n import JavaScriptCatalog

from aurora.i18n.engine import translator

LANGUAGE_QUERY_PARAMETER = "language"


@login_required()
def editor_info(request):
    data = {
        "authenticated": request.user.is_authenticated,
        "staff": request.user.is_staff,
        "canTranslate": request.user.is_staff,
        "languageCode": get_language(),
        "editUrl": reverse("admin:i18n_message_get_or_create"),
    }
    return JsonResponse(data)


class SmartJavascriptCatalog(JavaScriptCatalog):
    domain = "djangojs"
    packages = None

    def get_catalog(self):
        catalog: dict = super().get_catalog()
        current_locale = get_language()
        dictionary = translator[current_locale]
        catalog.update(dictionary.messages)
        return catalog

    @method_decorator(condition(lambda *a, **kw: cache.get("i18n")))
    def get(self, request, *args, **kwargs):
        return super().get(request)

    def render_to_response(self, context, **response_kwargs):
        return super().render_to_response(context, **response_kwargs)
