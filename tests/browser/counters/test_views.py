from datetime import date
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from django.urls import reverse
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


def test_counter_index(mock_state, browser: AuroraTestBrowser, data):
    reg: "Registration" = data[0].registration

    url = reverse("charts:index", args=[reg.project.organization.slug])
    browser.login()
    browser.open(url)


def test_counter_project_index(browser: AuroraTestBrowser, data):
    reg: "Registration" = data[0].registration

    url = reverse("charts:project-index", args=[reg.project.organization.slug, reg.project.pk])
    browser.login()
    browser.open(url)


def test_counter_registration(browser: AuroraTestBrowser, data):
    reg: "Registration" = data[0].registration

    url = reverse("charts:registration", args=[reg.project.organization.slug, reg.project.pk, reg.pk])
    browser.login()
    browser.open(url)
    browser.click("button#prev")
    browser.click("button#next")


def test_counter_monthly_data(browser: AuroraTestBrowser, data):
    reg: "Registration" = data[0].registration

    url = reverse("charts:monthly_data", args=[reg.project.organization.slug, reg.project.pk, reg.pk])
    browser.login()
    browser.open(url)
