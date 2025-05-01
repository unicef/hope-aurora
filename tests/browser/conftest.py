from typing import TYPE_CHECKING, Generator

import pytest
from seleniumbase import config as sb_config
from seleniumbase.core import session_helper

if TYPE_CHECKING:
    from testutils.selenium import AuroraSeleniumTC

    from aurora.state import State


@pytest.fixture
def mock_state(rf) -> Generator["State", None, None]:
    from aurora.state import state

    state.request = rf.get("/")
    yield state
    state.request = None


@pytest.fixture
def browser(live_server, request) -> "Generator[AuroraSeleniumTC, None, None]":
    """SeleniumBase as a pytest fixture.
    Usage example: "def test_one(sb):"
    You may need to use this for tests that use other pytest fixtures."""
    from testutils.selenium import AuroraSeleniumTC

    if request.cls:
        if sb_config.reuse_class_session:
            the_class = str(request.cls).split(".")[-1].split("'")[0]
            if the_class != sb_config._sb_class:
                session_helper.end_reused_class_session_as_needed()
                sb_config._sb_class = the_class
        request.cls.sb = AuroraSeleniumTC("base_method")
        request.cls.sb.live_server_url = str(live_server)
        request.cls.sb.setUp()
        request.cls.sb._needs_tearDown = True
        request.cls.sb._using_sb_fixture = True
        request.cls.sb._using_sb_fixture_class = True
        sb_config._sb_node[request.node.nodeid] = request.cls.sb
        yield request.cls.sb
        if request.cls.sb._needs_tearDown:
            request.cls.sb.tearDown()
            request.cls.sb._needs_tearDown = False
    else:
        sb = AuroraSeleniumTC("base_method")
        sb.live_server_url = str(live_server)
        sb.setUp()
        sb._needs_tearDown = True
        sb._using_sb_fixture = True
        sb._using_sb_fixture_no_class = True
        sb_config._sb_node[request.node.nodeid] = sb
        sb.maximize_window()
        yield sb
        if sb._needs_tearDown:
            sb.tearDown()
            sb._needs_tearDown = False


@pytest.fixture
def birth_after_1900(db):
    from testutils.factories import Validator, ValidatorFactory

    code = """
    var limit1 = Date.parse("1900-01-01");
    var today = new Date();
    var dt = Date.parse(value);
    if (dt < limit1)
        "the date should be after 1900";
    else
        if (dt > today)
            "the date should be before today";
        else
            true
    """
    return ValidatorFactory(name="birth_after_1900", target=Validator.FIELD, active=True, code=code)
