import logging
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse

from aurora.state import state

logger = logging.getLogger(__name__)


class ThreadLocalMiddleware:
    """Middleware that puts the request object in thread local storage."""

    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: "HttpRequest") -> "HttpResponse":
        state.request = request
        state.collect_messages = False

        ret = self.get_response(request)
        state.request = None
        return ret
