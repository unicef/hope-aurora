import pytest
from django.template import Context, Template, TemplateSyntaxError

from aurora.i18n.engine import translator

pytestmark = pytest.mark.django_db


def _render(rf, string, context=None, locale="en-us"):
    req = rf.get(f"/{locale}/")
    translator.activate(locale)
    data = {"request": req}
    if context:
        data.update(context)
    return Template(string).render(Context(data))


def test_translate_rejects_duplicate_option(rf):
    with pytest.raises(TemplateSyntaxError, match="specified more than once"):
        _render(rf, '{% load itrans %}{% translate "First Name" noop noop %}')


def test_blocktranslate_rejects_duplicate_option(rf):
    with pytest.raises(TemplateSyntaxError, match="specified more than once"):
        _render(rf, "{% load itrans %}{% blocktranslate trimmed trimmed %}x{% endblocktranslate %}")


def test_blocktranslate_rejects_count_without_plural(rf):
    with pytest.raises(TemplateSyntaxError, match="doesn't allow other block tags inside it"):
        _render(rf, "{% load itrans %}{% blocktranslate count c=1 %}x{% endblocktranslate %}")


def test_blocktranslate_unknown_argument(rf):
    with pytest.raises(TemplateSyntaxError, match="Unknown argument"):
        _render(rf, "{% load itrans %}{% blocktranslate uknownopt %}x{% endblocktranslate %}")


def test_bool_icon_filter_branches(rf):
    yes = _render(rf, "{% load itrans %}{{ 1|bool_icon }}")
    no = _render(rf, "{% load itrans %}{{ 0|bool_icon }}")
    assert "icon-yes.svg" in yes
    assert "icon-no.svg" in no
