from datetime import date
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from django.urls import reverse
from selenium.webdriver import ActionChains
from testutils.factories import CounterFactory, OrganizationFactory, ProjectFactory, RegistrationFactory
from testutils.selenium import AuroraTestBrowser

from aurora.counters.models import Counter

if TYPE_CHECKING:
    from aurora.registration.models import Registration

pytestmark = pytest.mark.selenium


@pytest.fixture
def mock_state():
    from django.contrib.auth.models import AnonymousUser

    from aurora.state import state

    state.request = Mock(user=AnonymousUser())
    yield
    state.request = None


@pytest.fixture
def data(db) -> list[Counter]:
    today = date.today()
    org = OrganizationFactory()
    prj = ProjectFactory(organization=org, slug="prj")
    reg = RegistrationFactory(project=prj)
    return [CounterFactory(day=date(today.year, today.month, day), registration=reg) for day in range(1, 28)]


def test_charts_user_navigation(browser: AuroraTestBrowser, admin_user, data):
    reg: "Registration" = data[0].registration
    url = reverse("charts:index")
    # with user_grant_permissions(user, "counters.view_counter", reg):
    browser.login_as_user()
    browser.open(url)
    browser.click_link_text(reg.organization.name)
    browser.click_link_text(reg.project.name)
    browser.click_link_text(reg.name)
    browser.click("button#prev")
    browser.click("button#next")
    canvas = browser.find_element("#myChart")
    location = canvas.location
    x = location["x"]
    y = location["y"]
    ActionChains(browser.driver).move_by_offset(x, y + 20).click(canvas).perform()
    browser.click("button#prev")
    browser.click("button#next")
    browser.find_element("div.breadcrumbs a.month").click()
    browser.click_link_text(reg.project.name)
    browser.click_link_text(reg.organization.name)
