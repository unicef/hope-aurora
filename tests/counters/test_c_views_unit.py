from datetime import date, datetime
from types import SimpleNamespace

from django.forms import Media
from django.http import HttpResponse
from aurora.counters.views import ChartIndex
from aurora.counters.views import DayChartView
from aurora.counters.views import MonthlyChartView
from aurora.counters.views import MonthlyDataView
from aurora.counters.views import OrganizationIndex
from aurora.counters.views import ProjectIndex


class FakeCounterQS:
    def __init__(self, records):
        self.records = records

    def order_by(self, *_args, **_kwargs):
        return self

    def filter(self, **kwargs):
        month = kwargs.get("day__month")
        if month:
            self.records = [r for r in self.records if r.day.month == month]
        return self

    def all(self):
        return self

    def count(self):
        return len(self.records)

    def __iter__(self):
        return iter(self.records)


def _request(rf, path="/", query=None):
    req = rf.get(path, data=query or {})
    req.user = SimpleNamespace(is_staff=False, is_superuser=False)
    return req


def test_index_contexts_respect_superuser_and_members(monkeypatch, rf):
    orgs = SimpleNamespace(order_by=lambda *_a, **_k: ["o1"])
    captured = []
    monkeypatch.setattr(
        "aurora.counters.views.Organization.objects.filter",
        lambda **kwargs: captured.append(kwargs) or orgs,
    )

    view = ChartIndex()
    view.request = _request(rf)
    view.request.user = SimpleNamespace(is_superuser=True, is_staff=True)
    ctx = view.get_context_data()
    assert ctx["organizations"] == ["o1"]
    assert captured[-1] == {}

    view.request.user = SimpleNamespace(is_superuser=False, is_staff=False)
    view.get_context_data()
    assert captured[-1] == {"members__user": view.request.user}


def test_organization_and_project_contexts(monkeypatch, rf):
    org = SimpleNamespace(
        projects=SimpleNamespace(filter=lambda **_k: ["p1"]),
    )
    project = SimpleNamespace(registrations=SimpleNamespace(filter=lambda **_k: ["r1"]))
    monkeypatch.setattr("aurora.counters.views.Organization.objects.get", lambda **_k: org)
    monkeypatch.setattr("aurora.counters.views.Project.objects.get", lambda **_k: project)

    org_view = OrganizationIndex()
    org_view.kwargs = {"org": "x"}
    org_view.request = _request(rf)
    org_view.request.user = SimpleNamespace(is_superuser=False, is_staff=False)
    org_ctx = org_view.get_context_data()
    assert org_ctx["organization"] is org
    assert org_ctx["projects"] == ["p1"]

    project_view = ProjectIndex()
    project_view.kwargs = {"org": "x", "prj": "2"}
    project_view.request = _request(rf)
    project_view.request.user = SimpleNamespace(is_superuser=False, is_staff=False)
    prj_ctx = project_view.get_context_data()
    assert prj_ctx["project"] is project
    assert prj_ctx["registrations"] == ["r1"]


def test_monthly_data_view_returns_aggregated_payload(monkeypatch, rf):
    reg = SimpleNamespace(__str__=lambda self: "Reg1")
    rec1 = SimpleNamespace(day=date(2026, 4, 1), records=2, pk=11)
    rec2 = SimpleNamespace(day=date(2026, 4, 2), records=3, pk=12)
    qs = FakeCounterQS([rec1, rec2])

    monkeypatch.setattr(
        "aurora.counters.views.Registration.objects.select_related",
        lambda: SimpleNamespace(get=lambda **_k: reg),
    )
    monkeypatch.setattr("aurora.counters.views.Counter.objects.filter", lambda **_k: qs)
    monkeypatch.setattr("aurora.counters.views.last_day_of_month", lambda d: d.replace(day=2))
    monkeypatch.setattr("aurora.counters.views.timezone.now", lambda: datetime(2026, 4, 10))

    view = MonthlyDataView()
    view.kwargs = {"org": "o", "prj": "1", "registration_id": "9"}
    request = _request(rf, query={"m": "2026-04-01"})
    response = view.get(request)
    assert response.status_code == 200
    assert b'"total": 5' in response.content
    assert b'"datapoints": 2' in response.content


def test_monthly_chart_and_day_chart_paths(monkeypatch, rf):
    counter_first = SimpleNamespace(day=date(2026, 1, 1))
    counter_last = SimpleNamespace(day=date(2026, 4, 1))
    reg = SimpleNamespace(
        project="proj",
        organization="org",
        counters=SimpleNamespace(
            first=lambda: counter_first,
            last=lambda: counter_last,
            filter=lambda **_k: SimpleNamespace(first=lambda: SimpleNamespace(pk=77)),
        ),
    )

    monkeypatch.setattr(
        "aurora.counters.views.Registration.objects.select_related",
        lambda: SimpleNamespace(get=lambda **_k: reg),
    )
    monkeypatch.setattr("aurora.counters.views.get_session_id", lambda: "tok-1")
    monkeypatch.setattr("aurora.counters.views.timezone.now", lambda: datetime(2026, 4, 10))
    monkeypatch.setattr("aurora.counters.views.render", lambda *_a, **_k: HttpResponse("ok"))

    monthly = MonthlyChartView()
    monthly.request = _request(rf, query={"m": "2026-04"})
    monthly.kwargs = {"org": "o", "prj": "1", "registration": "9"}
    ctx = monthly.get_context_data()
    assert ctx["month"] == 4
    assert ctx["year"] == 2026
    assert ctx["token"] == "tok-1"
    assert isinstance(monthly.media, Media)

    day = DayChartView()
    day.request = _request(rf, query={"day": "2026-04-03"})
    day.kwargs = {"org": "o", "prj": "1", "registration": "9"}
    day.__dict__["registration"] = reg
    response = day.get(day.request)
    assert response.status_code == 200
    assert day.original.pk == 77
