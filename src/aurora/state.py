from datetime import datetime
from threading import local


class State(local):
    request = None
    data = {"collect_messages": False, "hit_messages": False}

    def __init__(self):
        self.timestamp = datetime.now()

    def __repr__(self):
        return f"<State {id(self)} - {self.timestamp}>"

    @property
    def collect_messages(self):
        return self.data["collect_messages"]

    @collect_messages.setter
    def collect_messages(self, value):
        self.data["collect_messages"] = value


state = State()
