import base64

from django.template import Context, Template

from aurora.registration.templatetags.dump_record import (
    concat,
    dump,
    dump_dict,
    dump_list,
    is_base64,
    is_image,
    isdict,
    islist,
    isstring,
    lookup,
)


def test_escapescript():
    code = """{% load dump_record %}{% escapescript %}var a = 1{% endescapescript %}"""
    assert Template(code).render(Context({})) == "var a = 1"


def test_islist():
    assert islist([])


def test_isstring():
    assert isstring("")


def test_isdict():
    assert isdict({})


def test_dump():
    assert dump("")


def test_dump_list():
    assert dump_list([])


def test_dump_dict():
    assert dump_dict({})


def test_lookup():
    code = """{% load dump_record %}{{ d|lookup:"key" }}"""
    value = {"key": 1}
    assert Template(code).render(Context({"d": value})) == "1"

    assert lookup(value, "key") == 1


def test_is_image():
    assert not is_image("")
    assert not is_image(2)


def test_is_base64():
    assert not is_base64("abc")
    assert is_base64(base64.b64encode(b"a===").decode())


def test_concat():
    assert concat("a", "b") == "ab"
