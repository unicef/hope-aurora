import json
import time
from datetime import datetime
from decimal import Decimal

from aurora.core.utils import jsonfy, safe_json

LANGUAGES = {
    "english": "first",
    "ukrainian": "АаБбВвГгҐґДдЕеЄєЖжЗзИиІіЇїЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЬьЮюЯя",
    "chinese": "姓名",
    "japanese": "ファーストネーム",
    "arabic": "الاسم الأول",
    "BIG": "АаБбВвГгҐґДдЕеЄєЖжЗзИиІіЇїЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЬьЮюЯя" * 1024,
}

DATA_TYPES = [
    1,
    1.0,
    Decimal("1.0"),
    [],
    (),
    set(),
    {},
    datetime(2000, 1, 1),
    datetime(2000, 1, 1).date(),
    datetime(2000, 1, 1).time(),
    time.time(),
    b"byte",
]


def pytest_generate_tests(metafunc):
    idlist = []
    argvalues = []
    if "data" in metafunc.fixturenames:
        for _, data in enumerate(DATA_TYPES):
            argvalues.append(data)
            idlist.append(type(data).__name__)
        metafunc.parametrize("data", argvalues, ids=idlist)
    elif "string" in metafunc.fixturenames:
        for lbl, data in LANGUAGES.items():
            argvalues.append(data)
            idlist.append(lbl)
        metafunc.parametrize("string", argvalues, ids=idlist)


def test_datatype(data):
    assert json.loads(safe_json({"data": data}))


def test_encoding(string):
    assert json.loads(safe_json({"string": string}))["string"] == string


def test_jsonfy(string):
    assert jsonfy({"string": string}) == {"string": string}
