import base64

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from aurora.core.utils import (
    extract_content,
    merge_data,
    namify,
    underscore_to_camelcase,
    apply_nested,
    flatten_dict,
)
from aurora.registration.storage import Router


@pytest.mark.parametrize("v", ["underscore_to_camelcase", "underscore to camelcase", "underscore__to_camelcase"])
def test_underscore_to_camelcase(v):
    assert underscore_to_camelcase(v) == "UnderscoreToCamelcase"


@pytest.mark.parametrize("unicode", (True, False))
@pytest.mark.parametrize(
    "value,expected",
    (
        ("a-b", "a_b"),
        ("à-b", "a_b"),
        ("à-è-î-ô-ü", "a_e_i_o_u"),
    ),
)
def test_namify_allow_unicode(unicode, value, expected):
    assert namify(value, unicode) == expected


def test_storage_router_flat():
    f = SimpleUploadedFile("file", b"content")
    c = base64.b64encode(b"content")
    data = {"name": "pippo", "file": f}
    r = Router()
    fields, files = r.decompress(data)
    assert fields == {"name": "pippo"}, "fields do not match"
    assert files == {"file": c}, "files do not match"
    assert extract_content(r.compress(fields, files)) == extract_content(data)


def test_storage_router_nested1():
    f = SimpleUploadedFile("file", b"content")
    c = base64.b64encode(b"content")
    data = {"name": "pippo", "childs": [{"file": f}]}

    r = Router()
    fields, files = r.decompress(data)
    assert fields == {"name": "pippo", "childs": [{}]}, "fields do not match"
    assert files == {"childs": [{"file": c}]}, "files do not match"
    assert extract_content(r.compress(fields, files)) == extract_content(data)


def test_storage_router_nested2():
    f1 = SimpleUploadedFile("sample.txt", b"content")
    f2 = SimpleUploadedFile("sample.txt", b"content")
    c = base64.b64encode(b"content")
    data = {"name": "pippo", "childs": [{"file": f1}], "el": [{"file": f2}]}
    r = Router()
    fields, files = r.decompress(data)
    assert fields == {
        "name": "pippo",
        "childs": [{}],
        "el": [{}],
    }, "fields do not match"
    assert files == {"childs": [{"file": c}], "el": [{"file": c}]}, "files do not match"
    assert extract_content(r.compress(fields, files)) == extract_content(data)


def test_merge():
    d1 = {"a": "1", "b": 2, "d": [{"bb": 3}]}
    d2 = {"c": [1], "d": [{"aa": 2}], "aa": {"vv": 1}}
    assert merge_data(d1, d2) == {"a": "1", "b": 2, "c": [1], "d": [{"aa": 2, "bb": 3}], "aa": {"vv": 1}}


@pytest.mark.parametrize(
    "value,expected", [({"languages": ["1"], "name": "eeeeee"}, {"languages": ["1"], "name": "eeeeee"})]
)
def test_apply_nested(value, expected):
    assert apply_nested(value) == expected


sss1 = {
    "label": "Name",
    "code": "CZ020",
}

sss2 = {
    "label": "Name",
    "individuals": [sss1],
}
sss3 = {
    "label": "Name",
    "lang": ["russian", "hungarian"],
}

sss4 = {"label": "Name", "individuals": [{"label": "Name", "lang": ["russian", "hungarian"]}]}


def test_flatten_dict1():
    assert flatten_dict(sss1) == {"code": "CZ020", "label": "Name"}


def test_flatten_dict2():
    assert flatten_dict(sss2) == {
        "label": "Name",
        "individuals_0_code": "CZ020",
        "individuals_0_label": "Name",
    }


def test_flatten_dict3():
    assert flatten_dict(sss3) == {"label": "Name", "lang": "russian,hungarian"}


def test_flatten_dict4():
    assert flatten_dict(sss4) == {
        "label": "Name",
        "individuals_0_lang": "russian,hungarian",
        "individuals_0_label": "Name",
    }
