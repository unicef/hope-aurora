import io
import base64
from types import SimpleNamespace
from unittest import mock

from PIL import Image
from django.template import Context
from django.template.base import Node, NodeList, Token, TokenType

from aurora.registration.models import Registration
from aurora.security.models import User
from aurora.web.templatetags import aurora


def test_islist():
    assert aurora.islist([])
    assert aurora.islist(())
    assert not aurora.islist("")


def test_isstring():
    assert not aurora.isstring([])
    assert not aurora.isstring(())
    assert aurora.isstring("")


def test_isdict():
    assert not aurora.isdict([])
    assert not aurora.isdict(())
    assert aurora.isdict({})


def test_dump():
    assert aurora.dump(
        {
            "list": [],
            "int": 1,
            "float": 1.1,
            "str": "foo",
            "bool": True,
            "dict": {"a": 1, "b": 2},
        }
    )


def test_dump_list():
    assert aurora.dump_list([1, 2, 3])


def test_dump_dict():
    assert aurora.dump_dict({"a": 1, "b": 2})


def test_jsonfy():
    assert aurora.jsonfy({"a": 1, "b": 2})


def test_markdown():
    assert aurora.markdown("**aa**") == "<p><strong>aa</strong></p>"
    assert aurora.markdown("") == ""


def test_md():
    assert aurora.md("**aa**") == "<strong>aa</strong>"
    assert aurora.md("") == ""


def test_oneline():
    assert (
        aurora._oneline("""a
b
c
""")
        == "a;b;c;"
    )


def test_link():
    with mock.patch("aurora.state.state.request") as m:
        m.user = User()
        assert aurora.link(Registration(advanced={}))
        assert aurora.link(Registration(advanced={"attrs": {"class": "test"}}))


def test_escapescript_node_and_tag():
    node = aurora.EscapeScriptNode(NodeList([Node()]))
    node.nodelist.render = lambda _ctx: "<script>x</script>"
    assert node.render(Context()) == "<script>x<\\/script>"

    parser = SimpleNamespace(
        parse=lambda *_a, **_k: NodeList([]),
        delete_first_token=lambda: None,
    )
    token = Token(TokenType.BLOCK, "escapescript")
    parsed = aurora.escapescript(parser, token)
    assert isinstance(parsed, aurora.EscapeScriptNode)


def test_smart_attr_and_lookup(monkeypatch):
    field = SimpleNamespace(field=SimpleNamespace(flex_field=SimpleNamespace(advanced={"smart": {"label": "Hello"}})))
    monkeypatch.setattr("aurora.web.templatetags.aurora._", lambda s: f"T:{s}")
    assert aurora.smart_attr(field, "label") == "Hello"
    assert aurora.smart_attr(field, "label,true") == "T:Hello"
    assert aurora.lookup({"a": 1}, "a") == 1


def test_is_image_and_base64_branches():
    assert aurora.is_image("short") is False

    img = Image.new("RGB", (60, 60), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="BMP")
    encoded_png = base64.b64encode(buf.getvalue()).decode()
    assert aurora.is_image(encoded_png) is True

    encoded_non_image = base64.b64encode(b"x" * 300).decode()
    assert aurora.is_image(encoded_non_image) is False

    good = base64.b64encode(b"a").decode()
    assert aurora.is_base64(good) is not False
    assert aurora.is_base64("not-b64") is False


def test_is_base64_exception_path(monkeypatch):
    monkeypatch.setattr(
        "aurora.web.templatetags.aurora.re.match",
        lambda *_a, **_k: (_ for _ in ()).throw(ValueError("x")),
    )
    with mock.patch("aurora.web.templatetags.aurora.logger.exception") as log:
        assert aurora.is_base64("YWJj==") is False
        assert log.called
