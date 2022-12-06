import logging

from django.utils import translation
from django.utils.translation import get_language_from_request
from flags.state import flag_enabled

from aurora.state import state

logger = logging.getLogger(__name__)


class I18NMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = get_language_from_request(request, check_path=True)
        state.collect_messages = flag_enabled("I18N_COLLECT_MESSAGES", request=request)

        from aurora.i18n.engine import translator

        e = translator.activate(lang)
        if state.collect_messages:
            e.reset()

        ret = self.get_response(request)
        state.collect_messages = False
        translation.deactivate()
        return ret