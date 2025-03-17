import base64
from unittest import mock

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
    assert aurora._md("**aa**") == "<strong>aa</strong>"
    assert aurora._md("") == ""


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


def test_is_base64():
    assert not aurora.is_base64("abc")
    assert aurora.is_base64(base64.b64encode(b"a===").decode())
