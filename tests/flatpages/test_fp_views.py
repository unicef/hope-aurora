import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.http import Http404
from testutils.factories import FlatPageFactory

from aurora.flatpages.views import flatpage, render_flatpage


@pytest.fixture
def page(db) -> FlatPage:
    pg = FlatPageFactory(url="/url/")
    pg.sites.add(Site.objects.get_current())
    return pg


@pytest.mark.parametrize("url", ["test", "/test"])
def test_flatpages_404(rf, page, url, settings):
    req = rf.get(url)
    with pytest.raises(Http404):
        flatpage(req, url)
    settings.APPEND_SLASH = False
    with pytest.raises(Http404):
        flatpage(req, url)


@pytest.mark.parametrize("url", ["url", "/url", "/url/"])
def test_flatpages(rf, page, url):
    req = rf.get(url)
    assert flatpage(req, url)


def test_flatpage_append_slash_stays_on_site(rf, page, settings):
    settings.APPEND_SLASH = True
    req = rf.get("/url")
    response = flatpage(req, "/url")
    assert response.status_code == 301
    assert response["Location"] == "/url/"


def test_flatpage_rejects_protocol_relative_redirect(rf, db, settings):
    settings.APPEND_SLASH = True
    pg = FlatPageFactory(url="//evil.example/")
    pg.sites.add(Site.objects.get_current())
    req = rf.get("/")
    req.path = "//evil.example"
    with pytest.raises(Http404):
        flatpage(req, "//evil.example")


def test_flatpages_view(django_app, page: "FlatPage"):
    url = page.get_absolute_url()
    res = django_app.get(url)
    assert res.status_code == 200


def test_render_flatpage(rf, page: "FlatPage"):
    req = rf.get("/")
    req.user = AnonymousUser()
    assert render_flatpage(req, page)

    page.template_name = "flatpages/flatpage.html"
    assert render_flatpage(req, page)

    page.registration_required = True
    assert render_flatpage(req, page)
