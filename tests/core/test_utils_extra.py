import datetime
import decimal
from types import SimpleNamespace
from unittest.mock import Mock

from django import forms
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.test import RequestFactory
from django.utils import timezone

from aurora.core import utils
from aurora.core.utils import JSONEncoder


def test_has_token_from_headers_and_cookie(settings):
    settings.ROOT_TOKEN = "root-token"
    request = RequestFactory().get("/", HTTP_X_AURORA_TOKEN="root-token")
    assert utils.has_token(request) is True

    request = RequestFactory().get("/")
    request.COOKIES["x-aurora-token"] = "root-token"
    assert utils.has_token(request) is True

    request = RequestFactory().get("/")
    assert utils.has_token(request) is False


def test_is_root_respects_user_and_feature_flag(monkeypatch):
    user = SimpleNamespace(is_superuser=True)
    request = SimpleNamespace(user=user)
    monkeypatch.setattr(utils, "flag_enabled", lambda *args, **kwargs: True)
    assert utils.is_root(request) is True

    monkeypatch.setattr(utils, "flag_enabled", lambda *args, **kwargs: False)
    assert utils.is_root(request) is False
    assert utils.is_root(SimpleNamespace()) is False


def test_json_encoder_handles_common_types():
    encoder = JSONEncoder()
    dt = datetime.datetime(2026, 4, 22, 12, 30, 10, 123456, tzinfo=datetime.UTC)
    assert encoder.default(dt).endswith("Z")
    assert encoder.default(datetime.date(2026, 4, 22)) == "2026-04-22"
    assert encoder.default(datetime.time(12, 10, 3, 120000)) == "12:10:03.120"
    assert sorted(encoder.default({1, 2})) == [1, 2]
    assert encoder.default(decimal.Decimal("10.5")) == "10.5"
    assert encoder.default(memoryview(b"ab")) == b"YWI="
    assert encoder.default(b"abc") == "abc"
    assert encoder.default(ValueError("x")) == "x"


def test_json_encoder_file_and_skip_files():
    content = ContentFile(b"payload")
    encoder = JSONEncoder(skip_files=False)
    assert encoder.default(content) == b"payload"

    content = ContentFile(b"payload")
    encoder = JSONEncoder(skip_files=True)
    assert encoder.default(content) == "::file::"


def test_render_sets_response_content_and_cookies(monkeypatch):
    monkeypatch.setattr(utils.loader, "render_to_string", lambda *args, **kwargs: "hello")
    response = utils.render(RequestFactory().get("/"), "template.html", cookies={"a": "b"})
    assert response.content == b"hello"
    assert response.cookies["a"].value == "b"


def test_get_bookmarks_parses_markers_and_links(monkeypatch):
    monkeypatch.setattr(
        utils,
        "config",
        Mock(SMART_ADMIN_BOOKMARKS="--\n#Header\nadmin,\nview,label\na,b,c\na,b,c,d\n"),
    )
    quick_links = utils.get_bookmarks(RequestFactory().get("/"))
    assert "<hr/>" in quick_links[0]
    assert "Header" in quick_links[1]
    assert "viewlink" in quick_links[2]


def test_dict_helpers_and_client_ip():
    target = {"a": {"x": 1}}
    utils.dict_setdefault(target, {"a": {"y": 2}, "b": 3})
    assert target == {"a": {"x": 1, "y": 2}, "b": 3}

    nested = utils.dict_get_nested({}, "a.b.c")
    nested["value"] = 7
    assert nested == {"value": 7}

    request = RequestFactory().get("/")
    request.META["HTTP_X_FORWARDED_FOR"] = "1.2.3.4:443, 5.6.7.8"
    assert utils.get_client_ip(request) == "1.2.3.4"
    assert utils.get_client_ip(None) is None


def test_misc_helpers(monkeypatch):
    monkeypatch.setattr(utils.state, "collect_messages", True)
    monkeypatch.setattr(utils.time, "time", lambda: 123.0)
    etag_collect = utils.get_etag(RequestFactory().get("/"))
    assert isinstance(etag_collect, str)
    assert etag_collect

    monkeypatch.setattr(utils.state, "collect_messages", False)
    etag_normal = utils.get_etag(RequestFactory().get("/"), "a", "b")
    assert isinstance(etag_normal, str)
    assert etag_normal
    assert etag_collect != etag_normal

    assert utils.last_day_of_month(datetime.date(2026, 2, 10)) == datetime.date(2026, 2, 28)
    assert utils.merge_data({"x": []}, {"choices": [1, 2]})["choices"] == [1, 2]
    assert utils.total_size({"a": [1, 2, 3]}) > 0
    assert utils.oneline("a\r\nb\nc\rd") == "a;b;c;d"


def test_cache_aware_helpers_and_session(monkeypatch):
    request = RequestFactory().get("/")
    request.user = SimpleNamespace(is_authenticated=True)
    request.session = SimpleNamespace(session_key="sess-1")
    monkeypatch.setattr(utils.state, "request", request)
    monkeypatch.setattr(utils.state, "user", request.user, raising=False)

    assert utils.get_session_id(request) == "sess-1"
    assert utils.cache_aware_url(request, "/x") == "/x?s=sess-1"
    assert utils.cache_aware_reverse("registrations").endswith("?s=sess-1")

    request.user = SimpleNamespace(is_authenticated=False)
    assert utils.get_session_id(request) == ""


def test_system_cache_and_never_ever_cache(monkeypatch):
    monkeypatch.setattr(utils, "config", Mock(CACHE_VERSION="cfg-v1"))
    monkeypatch.setenv("VERSION", "v2")
    monkeypatch.setenv("BUILD_DATE", "2026-04-22")
    assert utils.get_system_cache_version() == "cfg-v1/v2/2026-04-22"

    decorated = utils.never_ever_cache(lambda *_args, **_kwargs: HttpResponse("ok"))
    response = decorated()
    assert response.status_code == 200
    assert "no-cache" in response.headers["Cache-Control"]


def test_flatten_and_build_dict():
    value = {
        "name": "A",
        "tags": ("x", "y"),
        "items": [{"a": "1"}, {"a": "2"}],
    }
    flat = utils.flatten_dict(value)
    assert flat["name"] == "A"
    assert flat["tags"] == "x,y"
    assert flat["items_0_a"] == "1"
    assert flat["items_1_a"] == "2"
    assert utils.flatten_dict("not-a-dict") == {}

    data = {
        "fields": {"a": "b"},
        "timestamp": timezone.now(),
        "id": 10,
        "ignored": False,
        "registration_id": 20,
    }
    built = utils.build_dict(data, datetime_format="Y-m-d")
    assert built["id"] == 10
    assert built["ignored"] is False
    assert built["code"].startswith("HOPE-")
    built_no_fmt = utils.build_dict(data)
    assert isinstance(built_no_fmt["timestamp"], str)


def test_fake_value_for_basic_fields():
    assert isinstance(utils.get_fake_value(forms.CharField()), str)
    assert isinstance(utils.get_fake_value(forms.IntegerField()), int)
    assert isinstance(utils.get_fake_value(forms.DateField()), str)
