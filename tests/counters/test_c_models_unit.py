from datetime import date, datetime, timezone as dt_timezone
from types import SimpleNamespace

from aurora.counters.models import Counter


class FakeSelection(list):
    def filter(self, **kwargs):
        if "id__in" in kwargs:
            wanted = set(kwargs["id__in"])
            return FakeSelection([r for r in self if r.id in wanted])
        return self


class FakeCounterFilter:
    def __init__(self, last_counter):
        self.last_counter = last_counter

    def order_by(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.last_counter


class FakeRecordQuery:
    def __init__(self, matches):
        self.matches = matches

    def annotate(self, **_kwargs):
        return self

    def values(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def all(self):
        return self.matches


def test_collect_uses_today_and_history_branches(monkeypatch):
    from aurora.counters import models as module

    reg1 = SimpleNamespace(id=1, slug="reg-1")
    reg2 = SimpleNamespace(id=2, slug="reg-2")
    selection = FakeSelection([reg1, reg2])
    monkeypatch.setattr(module.Registration.objects, "filter", lambda **_k: selection)

    monkeypatch.setattr(
        module.timezone,
        "now",
        lambda: datetime(2026, 4, 22, 10, 0, tzinfo=dt_timezone.utc),
    )

    # reg2 has a previous counter; reg1 is filtered out by registrations argument.
    monkeypatch.setattr(
        module.Counter.objects,
        "filter",
        lambda **kwargs: FakeCounterFilter(SimpleNamespace(day=date(2026, 4, 20)))
        if kwargs.get("registration") is reg2
        else FakeCounterFilter(None),
    )

    historical_matches = [
        {"day": date(2026, 4, 21), "hour": 1, "c": 2},
    ]
    today_matches = [
        {"day": date(2026, 4, 22), "hour": 5, "c": 3},
    ]
    record_calls = []

    def _record_filter(**kwargs):
        record_calls.append(kwargs)
        if "timestamp__gte" in kwargs:
            return FakeRecordQuery(today_matches)
        return FakeRecordQuery(historical_matches)

    monkeypatch.setattr(module.Record.objects, "filter", _record_filter)

    updated = []
    created = []
    monkeypatch.setattr(
        module.Counter.objects,
        "update_or_create",
        lambda **kwargs: updated.append(kwargs),
    )
    monkeypatch.setattr(
        module.Counter.objects,
        "get_or_create",
        lambda **kwargs: created.append(kwargs),
    )

    querysets, result = module.Counter.objects.collect(registrations=[2])

    assert len(querysets) == 1
    assert result["registration"] == 1
    assert result["records"] == 5
    assert result["days"] == 2
    assert result["details"]["reg-2"]["days"] == 2
    assert len(updated) == 1
    assert len(created) == 1
    assert any("timestamp__range" in call for call in record_calls)
    assert any("timestamp__gte" in call for call in record_calls)


def test_counter_string_and_hourly_fallback():
    c = Counter(details={"hours": {"1": 7, "22": 2}})
    hourly = c.hourly
    assert len(hourly) == 23
    assert hourly[1] == 7
    assert hourly[22] == 2

    c.pk = 9
    assert str(c) == "Counter #9"
