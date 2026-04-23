import pytest
from django.template import Context, Template, TemplateSyntaxError
from django.test import RequestFactory

from aurora.i18n.engine import translator

pytestmark = pytest.mark.django_db


def _render(string, context=None, locale="en-us"):
    req = RequestFactory().get(f"/{locale}/")
    translator.activate(locale)
    data = {"request": req}
    if context:
        data.update(context)
    return Template(string).render(Context(data))


def test_translate_rejects_duplicate_option():
    with pytest.raises(TemplateSyntaxError, match="specified more than once"):
        _render('{% load itrans %}{% translate "First Name" noop noop %}')


def test_blocktranslate_rejects_duplicate_option():
    with pytest.raises(TemplateSyntaxError, match="specified more than once"):
        _render("{% load itrans %}{% blocktranslate trimmed trimmed %}x{% endblocktranslate %}")


def test_blocktranslate_rejects_count_without_plural():
    with pytest.raises(TemplateSyntaxError, match="doesn't allow other block tags inside it"):
        _render("{% load itrans %}{% blocktranslate count c=1 %}x{% endblocktranslate %}")


def test_blocktranslate_unknown_argument():
    with pytest.raises(TemplateSyntaxError, match="Unknown argument"):
        _render("{% load itrans %}{% blocktranslate uknownopt %}x{% endblocktranslate %}")


def test_bool_icon_filter_branches():
    yes = _render("{% load itrans %}{{ 1|bool_icon }}")
    no = _render("{% load itrans %}{{ 0|bool_icon }}")
    assert "icon-yes.svg" in yes
    assert "icon-no.svg" in no
