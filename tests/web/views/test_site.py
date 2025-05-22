from pathlib import Path

import pytest
from django.urls import reverse
from django_webtest import DjangoTestApp
from testutils.factories import TemplateFactory

from aurora.web.views.sites import error_csrf


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
