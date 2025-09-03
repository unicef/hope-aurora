from typing import TYPE_CHECKING

import pytest
from django.contrib.auth.models import AnonymousUser
from django.template import Context, Template, TemplateSyntaxError
from django.test import RequestFactory
from testutils.factories import MessageFactory

from aurora.i18n.engine import translator

if TYPE_CHECKING:
    from aurora.i18n.models import Message


def _render_template(string, context=None, locale="en-us"):
    req = RequestFactory().get(f"/{locale}/")
    translator.activate(locale)
    req.user = AnonymousUser()
    context = context or {"k": "First Name", "request": req}
    context = Context(context)
    return Template(string).render(context)


@pytest.fixture
def data(db):
    m1: Message = MessageFactory(msgstr="First Name")
    m1.update_or_create_translation("Nome", "it", False)

    m2: Message = MessageFactory(msgstr="There is %(count)s object.")
    m2.update_or_create_translation("C'è %(count)s oggetto.", "it", False)

    m3: Message = MessageFactory(msgstr="There are %(count)s objects.")
    m3.update_or_create_translation("Ci sono %(count)s oggetti.", "it", False)


def test_translate(data):
    rendered = _render_template("""{% load itrans %}{% translate "First Name" %}""")
    assert rendered == "First Name"

    rendered = _render_template("""{% load itrans %}{% translate "First Name" %}""", locale="it")
    assert rendered == "Nome"


def test_translate_noop(data):
    rendered = _render_template("""{% load itrans %}{% translate k noop %}""")
    assert rendered == "First Name"


def test_translate_error(data):
    with pytest.raises(TemplateSyntaxError):
        _render_template("""{% load itrans %}{% translate k noop noop %}""")
    with pytest.raises(TemplateSyntaxError):
        _render_template("""{% load itrans %}{% translate k uknown %}""")

    with pytest.raises(TemplateSyntaxError):
        _render_template("""{% load itrans %}{% translate %}""")


def test_translate_context(data):
    rendered = _render_template("""{% load itrans %}{% translate "First Name" context "greeting" %}""")
    assert rendered == "First Name"
    with pytest.raises(TemplateSyntaxError):
        _render_template("""{% load itrans %}{% translate "First Name" context  %}""")
    with pytest.raises(TemplateSyntaxError):
        _render_template("""{% load itrans %}{% translate "First Name" context noop %}""")


def test_translate_expr(data):
    rendered = _render_template("""{% load itrans %}{% translate k %}""")
    assert rendered == "First Name"

    rendered = _render_template("""{% load itrans %}{% translate k %}""", locale="it")
    assert rendered == "Nome"


def test_translate_as_var(data):
    rendered = _render_template("""{% load itrans %}{% translate "First Name" as var %}{{ var }}""")
    assert rendered == "First Name"

    rendered = _render_template("""{% load itrans %}{% translate "First Name" as var %}{{ var }}""", locale="it")
    assert rendered == "Nome"
    with pytest.raises(TemplateSyntaxError):
        _render_template("""{% load itrans %}{% translate "First Name" as  %}{{ var }}""", locale="it")


# block_translate


def test_block_translate_error(data):
    with pytest.raises(TemplateSyntaxError):
        _render_template("""{% load itrans %}{% blocktranslate with a=1 with b=2 %}{% endblocktranslate %}""")
    with pytest.raises(TemplateSyntaxError):
        _render_template("""{% load itrans %}{% blocktranslate noop noop %}{% endblocktranslate %}""")
    with pytest.raises(TemplateSyntaxError):
        _render_template("""{% load itrans %}{% blocktranslate uknown %}{% endblocktranslate %}""")
    with pytest.raises(TemplateSyntaxError):
        _render_template("""{% load itrans %}{% blocktranslate with %}{% endblocktranslate %}""")
    with pytest.raises(TemplateSyntaxError):
        _render_template("""{% load itrans %}{% blocktranslate count %}{% endblocktranslate %}""")
    with pytest.raises(TemplateSyntaxError):
        _render_template("""{% load itrans %}{% blocktranslate context %}{% endblocktranslate %}""")
    with pytest.raises(TemplateSyntaxError):
        _render_template("""{% load itrans %}{% blocktranslate asvar %}{% endblocktranslate %}""")


def test_block_translate(data):
    tpl = """{% load itrans %}{% blocktranslate %}First Name{% endblocktranslate %}"""
    rendered = _render_template(tpl)
    assert rendered == "First Name"

    rendered = _render_template(tpl, locale="it")
    assert rendered == "Nome"


def test_block_translate_trimmed(data):
    tpl = """{% load itrans %}{% blocktranslate with aa=k trimmed %}{{ aa }}   {% endblocktranslate %}"""
    rendered = _render_template(tpl)
    assert rendered == "First Name"

    rendered = _render_template(tpl, locale="it")
    assert rendered == "Nome"


def test_block_translate_with(data):
    tpl = """{% load itrans %}{% blocktranslate with aa=k %}{{ aa }}{% endblocktranslate %}"""
    rendered = _render_template(tpl)
    assert rendered == "First Name"

    rendered = _render_template(tpl, locale="it")
    assert rendered == "Nome"


def test_block_translate_expr(data):
    tpl = """{% load itrans %}{% blocktranslate %}{{ k }}{% endblocktranslate %}"""
    rendered = _render_template(tpl)
    assert rendered == "First Name"

    rendered = _render_template(tpl, locale="it")
    assert rendered == "Nome"


def test_block_translate_as_var(data):
    tpl = """{% load itrans %}{% blocktranslate with aa=k|lower asvar ccc %}={{aa}}={% endblocktranslate %}{{ ccc }}"""
    rendered = _render_template(tpl)
    assert rendered == "=first name="

    rendered = _render_template(tpl, locale="it")
    assert rendered == "=first name="


def test_block_translate_count(data):
    tpl = """{% load itrans %}{% blocktranslate count count=var|length %}
There is {{ count }} object.{% plural %}There are {{ count }} objects.{% endblocktranslate %}"""
    rendered = _render_template(tpl, context={"var": "abc"})
    assert "There are 3 objects" in rendered

    rendered = _render_template(tpl, context={"var": "a"})
    assert "There is 1 object" in rendered

    rendered = _render_template(tpl, locale="it", context={"var": "abc"})
    assert "Ci sono 3 oggetti." in rendered


def test_md5(data):
    tpl = """{% load itrans %}{{ "First Name"|md5:"it-it" }}"""
    assert _render_template(tpl) == "c746cb9d2a1d62ece08e03ea0f789004"


def test_msgcode(data):
    tpl = """{% load itrans %}{{ "First Name"|msgcode  }}"""
    assert _render_template(tpl) == "b3b358e690289684023f60990a582858"


def test_strip(data):
    tpl = """{% load itrans %}{{ "First Name   "|strip }}"""
    assert _render_template(tpl) == "First Name"


def test_bool_icon(data):
    tpl = """{% load itrans %}{{ True|bool_icon }}"""
    assert _render_template(tpl) == '<img src="/static/admin/img/icon-yes.svg" alt="True">'

    tpl = """{% load itrans %}{{ False|bool_icon }}"""
    assert _render_template(tpl) == '<img src="/static/admin/img/icon-no.svg" alt="False">'
