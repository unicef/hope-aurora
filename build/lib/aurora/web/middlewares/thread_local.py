import logging

from aurora.state import state

logger = logging.getLogger(__name__)


class ThreadLocalMiddleware:
    """Middleware that puts the request object in thread local storage."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        state.request = request
        state.collect_messages = False

        ret = self.get_response(request)
        state.request = None
        return ret
