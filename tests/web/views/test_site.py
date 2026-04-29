from pathlib import Path
from types import SimpleNamespace

import pytest
from django.http import HttpResponse
from django.urls import reverse
from django_webtest import DjangoTestApp
from testutils.factories import TemplateFactory

from aurora.web.views.sites import error_csrf
from aurora.web.views.sites import error_404
from aurora.web.views.sites import get_active_registrations
from aurora.web.views.sites import HomeView
from aurora.web.views.sites import PageView
from aurora.web.views.sites import QRCodeView


@pytest.fixture
def app(django_app_factory):
    return django_app_factory(csrf_checks=False)


@pytest.mark.parametrize("verb", ["get", "head", "post"])
def test_probe_view(db, django_app: DjangoTestApp, verb):
    url = "/probe/"  # do not reverse this
    method = getattr(django_app, verb)
    assert method(url).status_code == 200


def test_home(db, django_app: DjangoTestApp):
    url = reverse("index")
    res = django_app.get(url)
    assert res.status_code == 200
    assert res.headers["Etag"]


def test_error_404(db, django_app: DjangoTestApp):
    res = django_app.get("/xza/", expect_errors=True)
    assert res.status_code == 404


def test_error_404_sets_session_header(rf):
    req = rf.get("/")
    response = error_404(req, Exception("missing"))
    assert response.status_code == 404
    assert response.headers["Session-Token"]


def test_offline(db, django_app: DjangoTestApp):
    url = reverse("offline")
    res = django_app.get(url)
    assert res.status_code == 200


def test_error_csrf(rf):
    req = rf.get("/")
    assert error_csrf(req)
    assert error_csrf(req, "reason")


def test_qrcode(db, django_app: DjangoTestApp):
    url = reverse("qrcode")
    res = django_app.get(url)
    assert res.status_code == 200


def test_template_page(db, django_app: DjangoTestApp):
    tpl = TemplateFactory()
    url = reverse("page", args=[Path(tpl.name).stem])
    res = django_app.get(url)
    assert res.status_code == 200


@pytest.mark.django_db
def test_get_active_registrations_filters_active_and_homepage():
    from testutils.factories import RegistrationFactory

    visible = RegistrationFactory(active=True, show_in_homepage=True)
    RegistrationFactory(active=True, show_in_homepage=False)
    RegistrationFactory(active=False, show_in_homepage=True)

    qs = get_active_registrations()
    assert list(qs) == [visible]


def test_page_view_template_and_context(monkeypatch, rf):
    view = PageView()
    view.kwargs = {"page": "custom-page"}
    view.request = rf.get("/")
    view.request.user = SimpleNamespace(is_staff=False)
    monkeypatch.setattr(
        "aurora.web.views.sites.get_active_registrations",
        lambda: ["r1", "r2"],
    )
    monkeypatch.setattr("aurora.i18n.get_text.gettext", lambda s: f"T:{s}")

    assert view.get_template_names() == ["custom-page.html"]
    ctx = view.get_context_data(extra=1)
    assert ctx["title"] == "Title"
    assert ctx["title2"] == "T:Title2"
    assert ctx["registrations"] == ["r1", "r2"]
    assert ctx["extra"] == 1


def test_home_view_template_names(monkeypatch):
    monkeypatch.setattr(
        "aurora.web.views.sites.config",
        SimpleNamespace(HOME_TEMPLATE="from-constance.html", CACHE_VERSION="v1"),
    )
    view = HomeView()
    assert view.get_template_names() == ["from-constance.html", "home.html"]


def test_home_view_get_conditional_and_uncached_paths(monkeypatch, rf):
    from aurora.web.views import sites

    req = rf.get("/")
    req.user = SimpleNamespace(is_staff=False)
    monkeypatch.setattr(
        "aurora.web.views.sites.config",
        SimpleNamespace(HOME_TEMPLATE="from-constance.html", CACHE_VERSION="v1"),
    )
    view = HomeView()

    monkeypatch.setattr(sites, "get_etag", lambda *_a, **_k: "etag-x")

    cached_response = HttpResponse("cached", status=304)
    monkeypatch.setattr(sites, "get_conditional_response", lambda *_a, **_k: cached_response)
    response = view.get(req)
    assert response.status_code == 304

    monkeypatch.setattr(sites, "get_conditional_response", lambda *_a, **_k: None)
    monkeypatch.setattr(
        "aurora.web.views.sites.TemplateView.get",
        lambda *_a, **_k: HttpResponse("fresh"),
    )
    response = view.get(req)
    assert response.status_code == 200
    assert response.headers["ETag"] == "etag-x"


def test_home_get_context_data_includes_registrations(monkeypatch, rf):
    view = HomeView()
    view.request = rf.get("/")
    view.request.user = SimpleNamespace(is_staff=False)
    monkeypatch.setattr("aurora.web.views.sites.get_active_registrations", lambda: ["r1"])
    ctx = view.get_context_data(extra="ok")
    assert ctx["registrations"] == ["r1"]
    assert ctx["extra"] == "ok"


def test_qrcode_context_uses_absolute_url(monkeypatch, rf):
    view = QRCodeView()
    request = rf.get("/")
    request.build_absolute_uri = lambda _p="/": "http://test/"
    view.request = request
    monkeypatch.setattr("aurora.web.views.sites.get_qrcode", lambda url: f"qr:{url}")

    ctx = view.get_context_data()
    assert ctx["url"] == "http://test/"
    assert ctx["qrcode"] == "qr:http://test/"
