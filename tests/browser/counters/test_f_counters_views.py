from datetime import date
from typing import TYPE_CHECKING

import pytest
from django.urls import reverse
from testutils.factories import CounterFactory, OrganizationFactory, ProjectFactory, RegistrationFactory
from testutils.selenium import AuroraTestBrowser

from aurora.counters.models import Counter

if TYPE_CHECKING:
    from aurora.registration.models import Registration

pytestmark = pytest.mark.selenium


@pytest.fixture
def data(db) -> list[Counter]:
    today = date.today()
    org = OrganizationFactory()
    prj = ProjectFactory(organization=org, slug="prj")
    reg = RegistrationFactory(project=prj)
    return [CounterFactory(day=date(today.year, today.month, day), registration=reg) for day in range(1, 28)]


@pytest.mark.xfail
def test_charts_user_navigation(browser: AuroraTestBrowser, admin_user, data):
    reg: "Registration" = data[0].registration
    url = reverse("charts:index")
    browser.login_as_user()
    browser.maximize_window()
    browser.open(url)
    browser.click_link_text(reg.organization.name)
    browser.click_link_text(reg.project.name)
    browser.click_link_text(reg.name)
    browser.click("button#prev")
    browser.click("button#next")
    browser.scroll_to_top()
    # mark the point just for debugging purpose. To find int in the screenshot
    browser.click_with_offset("#myChart", 60, 200, mark=True)
    browser.scroll_to_top()
    browser.click("button#prev")
    browser.click("button#next")
    browser.scroll_to_top()
    browser.click_link_text(reg.project.name)
    browser.scroll_to_top()
    browser.click_link_text(reg.organization.name)
