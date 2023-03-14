import json
from collections import defaultdict
from urllib import parse

from channels.generic.websocket import WebsocketConsumer
from django.core.cache import caches
from django.urls import path

cache = caches["default"]


class FieldEditorConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data=None, bytes_data=None):
        data = dict(parse.parse_qsl(text_data))
        data.pop("csrfmiddlewaretoken")
        config = defaultdict(dict)
        for name, value in data.items():
            prefix, field_name = name.split("-")
            config[prefix][field_name] = value
        cache.set(self.scope["path"], config)
        self.send(text_data=json.dumps({"message": data}))


class FieldWidgetConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data=None, bytes_data=None):
        data = parse.parse_qs(text_data)
        self.send(text_data=json.dumps({"message": data}))


websocket_urlpatterns = [
    path("editor/field/<int:user_pk>/<int:field>/", FieldEditorConsumer.as_asgi()),
    path("widget/field/<int:user_pk>/<int:field>/", FieldWidgetConsumer.as_asgi()),
]
