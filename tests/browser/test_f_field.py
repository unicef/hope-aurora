import pytest
from strategy_field.utils import fqn

from aurora.core.fields import HiddenField, LocationField, CompilationTimeField
from testutils.factories import FormFactory
from testutils.selenium import AuroraTestBrowser

from aurora.core.models import FlexFormField

pytestmark = pytest.mark.selenium


def pytest_generate_tests(metafunc):
    idlist = []
    argvalues = []
    from aurora.core.registry import field_registry

    for field in field_registry:
        idlist.append(fqn(field.__name__))
        argvalues.append(field)

    metafunc.parametrize("field_type", argvalues, ids=idlist, scope="class")


def test_add_field(browser: AuroraTestBrowser, field_type):
    main = browser.driver.current_window_handle

    form = FormFactory()
    browser.open("/admin/")
    browser.login()
    browser.click_link("Flex Fields")
    browser.click('a:contains("Add Flex Field")')
    browser.select2_select("id_flex_form", form.name)
    browser.type("input#id_label", "FlexField-Test")
    browser.type("input#id_name", "flex_field_test")
    browser.select2_select("id_field_type", field_type.__name__)
    browser.click('input[name="_save"]')
    browser.wait_for_ready_state_complete()
    browser.click_link("FlexField-Test")
    browser.click('a:contains("editor")')
    browser.click("#radio_code")
    browser.click("#radio_attrs")
    browser.click("#radio_display")
    browser.click('a:contains("Form Field attributes")')
    browser.click('a:contains("Widget Field attributes")')
    browser.click('a:contains("Smart Field attributes")')
    if field_type not in [HiddenField, LocationField, CompilationTimeField]:
        browser.type("input[name=smart-question]", "Question")
        browser.switch_to_frame("#widget_display")
        browser.wait_for_ready_state_complete()
        browser.switch_to_window(main)
        browser.wait_for_ready_state_complete()

    browser.click('a:contains("CSS Field attributes")')
    browser.click('a:contains("Events")')
    browser.click('a:contains("Usage")')
    browser.open_if_not_url("/admin/")
    assert FlexFormField.objects.filter(label="FlexField-Test").exists()
