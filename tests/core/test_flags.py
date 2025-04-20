from contextlib import nullcontext as does_not_raise
from unittest.mock import Mock

import pytest
from django.core.exceptions import ValidationError

from aurora.core.flags import client_ip, cookie, debug, localhost, parse_bool, request_header, user_field, validate_bool


@pytest.mark.parametrize("value", ["1", "y", "Yes", "T", "True", "ON"])
def test_parse_bool_true(value):
    assert parse_bool(value)


@pytest.mark.parametrize("value", ["n", "no"])
def test_parse_bool_false(value):
    assert not parse_bool(value)


@pytest.mark.parametrize(
    ["value", "expectation"],
    [
        ("true", does_not_raise()),
        ("false", does_not_raise()),
        (0, pytest.raises(ValidationError)),
        ("t", pytest.raises(ValidationError)),
    ],
    ids=["true", "false", "0", "t"],
)
def test_validate_bool(value, expectation):
    with expectation:
        validate_bool(value)


def test_localhost(rf):
    req = rf.get("/", HTTP_HOST="localhost")
    assert localhost("/", req)


def test_debug():
    assert not debug("true")


@pytest.mark.parametrize("value", [True, False])
def test_user_field(admin_user, value):
    req = Mock(user=admin_user)
    assert user_field(f"username={admin_user.username}", req)
    assert not user_field("123", req)


def test_client_ip(rf):
    req = rf.get("/", REMOTE_ADDR="localhost")

    assert client_ip("localhost", req)
    assert not client_ip("127.0.0.1", req)


def test_request_header(rf):
    req = rf.get("/", HTTP_REMOTE_ADDR="localhost")

    assert request_header("REMOTE_ADDR=localhost", req)
    assert not request_header("localhost", req)


def test_cookie(rf):
    req = rf.get("/", HTTP_REMOTE_ADDR="localhost")
    req.COOKIES["thing"] = "whatever"
    assert cookie("thing=whatever", req)
    assert not cookie("localhost", req)
