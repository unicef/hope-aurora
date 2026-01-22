import pytest
from django.urls import reverse
from strategy_field.utils import fqn
from testutils.factories import FlexFormFieldFactory, FormFactory
from testutils.selenium import AuroraTestBrowser

from aurora.core.fields import (
    BooleanField,
    CompilationTimeField,
    DurationField,
    HiddenField,
    LocationField,
    MultiCheckboxField,
)
from aurora.core.models import FlexFormField

pytestmark = pytest.mark.selenium


def pytest_generate_tests(metafunc):
    idlist = []
    argvalues = []
    from aurora.core.registry import field_registry

    if "field_type" in metafunc.fixturenames:
        for field in field_registry:
            if hasattr(field, "custom"):
                continue
            idlist.append(fqn(field.__name__))
            argvalues.append(field)

        metafunc.parametrize("field_type", argvalues, ids=idlist, scope="class")


def test_add_field(browser: AuroraTestBrowser, field_type):
    main = browser.driver.current_window_handle
    form = FormFactory()
    browser.login()
    add_url = reverse("admin:core_flexformfield_add")
    browser.open(add_url)

    browser.select2_select("id_flex_form", form.name)
    browser.send_keys("input#id_label", "FlexField-Test")
    browser.send_keys("input#id_name", "flex_field_test")
    browser.select2_select("id_field_type", field_type.__name__)
    browser.click('input[name="_save"]')
    browser.wait_for_ready_state_complete()
    browser.click_link("FlexField-Test")
    if field_type not in [HiddenField, LocationField, CompilationTimeField, DurationField]:
        browser.click('a:contains("editor")')
        browser.click("#radio_code")
        browser.click("#radio_attrs")
        browser.click("#radio_display")
        browser.click('a:contains("Form Field attributes")')
        browser.click('a:contains("Widget Field attributes")')
        browser.click('a:contains("Smart Field attributes")')
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
    browser.switch_to_window(main)


@pytest.mark.flaky(reruns=2, only_rerun=["AssertionError"])
@pytest.mark.xfail
def test_boolean_field(browser: AuroraTestBrowser):
    form = FormFactory()
    fld: FlexFormField = FlexFormFieldFactory(
        flex_form=form,
        label="FlexField1",
        name="flexfield-bool1",
        field_type=BooleanField,
        advanced={"smart": {"visible": True}},
    )
    browser.login()
    browser.click_link("Flex Fields")
    browser.click_link(fld.label)

    browser.click('a:contains("editor")')
    browser.click("#radio_display")
    browser.switch_to_frame("#widget_display")
    browser.click(f"input[type=checkbox][name={fld.name}]")
    browser.click("input[type=submit]")
    browser.wait_for_ready_state_complete()
    browser.assert_exact_text("Success", "div.bg-green-200", timeout=20)


def test_multicheckboxfield_field(browser: AuroraTestBrowser):
    main = browser.driver.current_window_handle
    form = FormFactory()
    fld: FlexFormField = FlexFormFieldFactory(
        flex_form=form,
        label="FlexField1",
        name="flexfield-mc1",
        field_type=MultiCheckboxField,
        choices="a,b,c",
        advanced={"smart": {"visible": True}},
    )
    browser.login()
    browser.click_link("Flex Fields")
    browser.click_link(fld.label)

    browser.click('a:contains("editor")')
    browser.click("#radio_display")
    browser.switch_to_frame("#widget_display")
    browser.wait_for_ready_state_complete()

    browser.click("input[type=checkbox][value=a]")
    browser.click("input[type=submit]")
    browser.wait_for_ready_state_complete()
    browser.assert_exact_text("Success", "div.bg-green-200")
    browser.switch_to_window(main)
