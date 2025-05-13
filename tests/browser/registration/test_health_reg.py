import pytest
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from aurora.registration.models import Registration
from aurora.core.cache import cache
from django.core.management import call_command

from testutils.selenium import AuroraTestBrowser

pytestmark = pytest.mark.selenium


@pytest.fixture
def health_registration(db):
    """
    Loads data from 'custom.json' fixture and returns the
    'Country1 Health Registration' Registration object.
    """
    call_command("loaddata", "tests/fixtures/custom.json")
    try:
        return Registration.objects.get(name="Country1 Health Registration")
    except Registration.DoesNotExist:
        pytest.fail(
            "The 'Country1 Health Registration' was not found after loading 'tests/fixtures/custom.json'. "
            "Please ensure the 'name' field in the JSON matches exactly."
        )


def _verify_formset_title_visibility(browser: AuroraTestBrowser, title: str):
    """Helper to verify formset title visibility."""
    selector = f"div[data-msgid='{title}']"
    assert browser.is_element_present(selector), (
        f"FormSet title container for '{title}' (selector: '{selector}') not found in the DOM."
    )
    assert browser.is_element_visible(selector), (
        f"FormSet title container for '{title}' '{selector}' found in the DOM but is not visible."
    )


def test_health_registration_correct_submission(
    browser: AuroraTestBrowser,
    health_registration: Registration,
):
    """
    Tests the correct submission scenario for health registration.
    """
    cache.clear()

    # Scenario 1: Correct health registration
    browser.open(health_registration.get_absolute_url())
    formsets_qs = health_registration.flex_form.formsets.filter(enabled=True).order_by("ordering")
    all_formset_titles = [fs.title for fs in formsets_qs]

    assert len(all_formset_titles) >= 2, (
        f"Expected at least 2 enabled formsets with titles for health_registration, "
        f"but found {len(all_formset_titles)}. Titles found: {all_formset_titles}"
    )

    _verify_formset_title_visibility(browser, all_formset_titles[0])
    _verify_formset_title_visibility(browser, all_formset_titles[1])

    enumerator_code_name = "intro-and-consent-0-enumerator_code"
    browser.find_element(f"input[name='{enumerator_code_name}']").send_keys("VWSBau3396")

    who_to_register_name = "intro-and-consent-0-who_to_register"
    who_to_register_value = "myself"
    browser.find_element(f"input[name='{who_to_register_name}'][value='{who_to_register_value}']").click()
    consent_checkbox_name = "intro-and-consent-0-consent_h_c"
    browser.find_element(f"input[name='{consent_checkbox_name}']").click()

    admin_fields_correct = [
        ("id_household-info-0-admin1_h_c", "Abia", "State"),
        ("id_household-info-0-admin2_h_c", "Aba North", "LGA"),
        ("id_household-info-0-admin3_h_c", "Ariaria", "Ward"),
    ]

    for field_id, text_to_select, field_type in admin_fields_correct:
        try:
            browser.select2_select(field_id, text_to_select)
            browser.sleep(1)
        except NoSuchElementException:
            if field_type == "State":
                admin2_field_info = next(
                    (
                        f
                        for f in health_registration.flex_form.get_form_class()
                        .base_fields["household-info"]
                        .form.flex_form.fields
                        if f.name == "admin2_h_c"
                    ),
                    None,
                )
                if admin2_field_info and admin2_field_info.required:
                    pytest.fail(
                        f"Field '{field_id}' ({field_type}) not found, but it's a dependency for required field"
                    )
            pytest.fail(f"Required field '{field_id}' ({field_type}) not found on the form.")

    submit_button_selector = "//input[@type='submit' and @data-msgid='Save']"
    browser.find_element(submit_button_selector, by="xpath").click()
    register_another_selector = "a[data-msgid='register another household']"
    browser.wait_for_text("Register Another Household", selector=register_another_selector, timeout=5)


def test_health_registration_invalid_submission(
    browser: AuroraTestBrowser,
    health_registration: Registration,
):
    """
    Tests the invalid submission scenario for health registration.
    """
    # Scenario 2: Invalid health registration
    # Re-open the URL to ensure a fresh form state for the invalid scenario
    browser.open(health_registration.get_absolute_url())
    formsets_qs_invalid = health_registration.flex_form.formsets.filter(enabled=True).order_by("ordering")
    all_formset_titles_invalid = [fs.title for fs in formsets_qs_invalid]

    assert len(all_formset_titles_invalid) >= 2, (
        f"Expected at least 2 enabled formsets with titles for health_registration, "
        f"but found {len(all_formset_titles_invalid)}. Titles found: {all_formset_titles_invalid}"
    )

    _verify_formset_title_visibility(browser, all_formset_titles_invalid[0])
    _verify_formset_title_visibility(browser, all_formset_titles_invalid[1])

    enumerator_code_name_invalid = "intro-and-consent-0-enumerator_code"
    enumerator_code_selector_invalid = f"input[name='{enumerator_code_name_invalid}']"
    browser.assert_element_present(enumerator_code_selector_invalid)
    browser.type(enumerator_code_selector_invalid, "INVALIDCODE")

    who_to_register_name_invalid = "intro-and-consent-0-who_to_register"
    who_to_register_selector_invalid = f"input[name='{who_to_register_name_invalid}'][value='myself']"
    browser.assert_element_present(who_to_register_selector_invalid)
    browser.click(who_to_register_selector_invalid)
    consent_checkbox_name_invalid = "intro-and-consent-0-consent_h_c"

    admin_fields_invalid = [
        ("id_household-info-0-admin1_h_c", "Abia", "State"),
        ("id_household-info-0-admin2_h_c", "Aba North", "LGA"),
        ("id_household-info-0-admin3_h_c", "Ariaria", "Ward"),
    ]

    for field_id, text_to_select, field_type in admin_fields_invalid:
        select2_container_selector = f"#{field_id}"
        try:
            browser.assert_element_present(select2_container_selector)
            browser.select2_select(field_id, text_to_select)
            browser.sleep(1)
        except WebDriverException as e:
            is_required = False
            if field_type == "State":
                admin2_field_info = next(
                    (
                        f
                        for f in health_registration.flex_form.get_form_class()
                        .base_fields["household-info"]
                        .form.flex_form.fields
                        if f.name == "admin2_h_c"
                    ),
                    None,
                )
                if admin2_field_info and admin2_field_info.required:
                    is_required = True
            elif field_type == "LGA":
                admin3_field_info = next(
                    (
                        f
                        for f in health_registration.flex_form.get_form_class()
                        .base_fields["household-info"]
                        .form.flex_form.fields
                        if f.name == "admin3_h_c"
                    ),
                    None,
                )
                if admin3_field_info and admin3_field_info.required:
                    is_required = True

            if is_required:
                pytest.fail(f"Required field '{field_id}' ({field_type}) not found or interaction failed: {e}")

    submit_button_selector_invalid = "//input[@type='submit' and @data-msgid='Save']"
    browser.assert_element_present(submit_button_selector_invalid, by="xpath")
    browser.click(submit_button_selector_invalid, by="xpath")

    enumerator_error_message = "Enter a valid value"
    enumerator_error_selector = f"#id_{enumerator_code_name_invalid}_error"
    browser.assert_text(enumerator_error_message, selector=enumerator_error_selector)

    consent_error_message = "This field is required."
    consent_error_selector = f"#id_{consent_checkbox_name_invalid}_error"
    browser.assert_text(consent_error_message, selector=consent_error_selector)
