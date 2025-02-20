from django.contrib.auth import login

from hijack import signals
from hijack.templatetags.hijack import can_hijack
from hijack.views import get_used_backend, keep_session_age


def is_hijacked():
    pass


def can_impersonate(hijacker, hijacked):
    return not hijacker.is_hijacked


def impersonate(request, hijacked):
    if can_hijack(request.user, hijacked):
        hijacker = request.user

        hijack_history = request.session.get("hijack_history", [])
        hijack_history.append(request.user._meta.pk.value_to_string(hijacker))

        backend = get_used_backend(request)
        backend = f"{backend.__module__}.{backend.__class__.__name__}"

        with signals.no_update_last_login(), keep_session_age(request.session):
            login(request, hijacked, backend=backend)

        request.session["hijack_history"] = hijack_history

        signals.hijack_started.send(
            sender=None,
            request=request,
            hijacker=hijacker,
            hijacked=hijacked,
        )
        return hijacked
    return None
