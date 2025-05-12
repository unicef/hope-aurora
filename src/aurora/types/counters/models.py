from typing import TypedDict


class CollectCounter(TypedDict):
    records: int
    extra: dict


class CollectRegDetail(TypedDict):
    range: list
    days: int


class CollectResult(TypedDict):
    registration: int
    records: int
    days: int
    details: dict[str, CollectRegDetail]
