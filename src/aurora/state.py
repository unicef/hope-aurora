from datetime import datetime
from threading import local

from django.http import HttpRequest


class State(local):
    request: HttpRequest | None = None
    data = {"collect_messages": False, "hit_messages": False}

    def __init__(self) -> None:
        self.timestamp = datetime.now()

    def __repr__(self) -> str:
        return f"<State {id(self)} - {self.timestamp}>"

    @property
    def collect_messages(self) -> bool:
        return self.data["collect_messages"]

    @collect_messages.setter
    def collect_messages(self, value: bool) -> None:
        self.data["collect_messages"] = value


state = State()
