import pytest
from django.contrib.auth.models import AnonymousUser
from django.template import Context, Template
from django.test import RequestFactory


def render_template(string, context=None):
    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    context = context or {"k": "it-it", "request": req}
    context = Context(context)
    return Template(string).render(context)


def test_translate_url():
    rendered = render_template("""{% load hreflang %}{% translate_url k %}{{ k }}""")
    assert rendered == "/it-it"


def test_translate_url_view_name(db):
    rendered = render_template("""{% load hreflang %}{% translate_url k view_name='index' %}{{ k }}""")
    assert rendered == "/it-it"


def test_translate_url_error():
    with pytest.raises(Exception, match="translate_url needs request context"):
        render_template("""{% load hreflang %}{% translate_url k %}{{ k }}""", {"k": "it-it"})
