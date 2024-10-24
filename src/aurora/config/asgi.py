import os

# from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

# from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter

# import aurora.core.channels

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aurora.config.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        #     # Just HTTP for now. (We can add other protocols later.)
        #     "websocket": AllowedHostsOriginValidator(
        #         AuthMiddlewareStack(URLRouter(aurora.core.channels.websocket_urlpatterns))
        #     ),
    }
)
