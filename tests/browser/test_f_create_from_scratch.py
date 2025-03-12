import pytest
from seleniumbase import BaseCase
from testutils.selenium import AuroraTestBrowser

from aurora.core.models import Organization

BaseCase.main(__name__, __file__)  # Call pytest

pytestmark = pytest.mark.selenium


def test_full_flow(browser: AuroraTestBrowser):
    # create organization
    browser.open("/admin/")
    browser.login()

    browser.click_link("Organizations")
    browser.click('a:contains("Add organization")')
    browser.type("input[name=name]", "UNICEF")
    browser.submit('input[value="Save"]')
    assert Organization.objects.filter(name="UNICEF").exists()
    browser.open("/admin/")


"""
    # self.wait_for_ready_state_complete()

    # self.click_link("Flex Forms")
    # self.click('a:contains("Add Flex Form")')
    # self.select2_select("id_project", self.registration.project.name)
    # self.type("input#id_name", "Form-Test")
    # self.click('input[name="_save"]')
    # self.open_if_not_url("/admin/")
    # self.wait_for_ready_state_complete()
    # assert FlexForm.objects.filter(name="Form-Test").exists()
"""
