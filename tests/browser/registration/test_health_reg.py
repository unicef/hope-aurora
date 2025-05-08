import pytest
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from aurora.registration.models import Registration
from aurora.core.cache import cache
from testutils.selenium import AuroraTestBrowser

pytestmark = pytest.mark.selenium


def test_correct_health_registration(
    browser: AuroraTestBrowser,
    health_registration: Registration,
):
    cache.clear()
    browser.open(health_registration.get_absolute_url())
    formsets_qs = health_registration.flex_form.formsets.filter(enabled=True).order_by("ordering")
    all_formset_titles = [fs.title for fs in formsets_qs]

    assert len(all_formset_titles) >= 2, (
        f"Expected at least 2 enabled formsets with titles for health_registration, "
        f"but found {len(all_formset_titles)}. Titles found: {all_formset_titles}"
    )

    def verify_formset_title_visibility(title, index):
        selector = f"div[data-msgid='{title}']"
        assert browser.is_element_present(selector), (
            f"FormSet title container for '{title}' (selector: '{selector}') not found in the DOM."
        )
        assert browser.is_element_visible(selector), (
            f"FormSet title container for '{title}' '{selector}' found in the DOM but is not visible."
        )

    verify_formset_title_visibility(all_formset_titles[0], 0)
    verify_formset_title_visibility(all_formset_titles[1], 1)

    enumerator_code_name = "intro-and-consent-0-enumerator_code"
    try:
        browser.find_element(f"input[name='{enumerator_code_name}']").send_keys("VWSBau3396")
    except NoSuchElementException:
        pytest.fail(f"Field '{enumerator_code_name}' not found on the form.")

    who_to_register_name = "intro-and-consent-0-who_to_register"
    who_to_register_value = "myself"
    browser.find_element(f"input[name='{who_to_register_name}'][value='{who_to_register_value}']").click()
    consent_checkbox_name = "intro-and-consent-0-consent_h_c"
    browser.find_element(f"input[name='{consent_checkbox_name}']").click()

    admin_fields = [
        ("id_household-info-0-admin1_h_c", "Abia", "State"),
        ("id_household-info-0-admin2_h_c", "Aba North", "LGA"),
        ("id_household-info-0-admin3_h_c", "Ariaria", "Ward"),
    ]

    for field_id, text_to_select, field_type in admin_fields:
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
    try:
        browser.find_element(submit_button_selector, by="xpath").click()
    except NoSuchElementException:
        pytest.fail(f"Save button (e.g., XPath '{submit_button_selector}') not found on the registration form.")

    register_another_selector = "a[data-msgid='register another household']"
    try:
        browser.wait_for_text("Register Another Household", selector=register_another_selector, timeout=5)
    except TimeoutException:
        pytest.fail(
            "Registration submission did not complete successfully - 'Register Another Household' link not found"
        )


def test_invalid_health_registration(
    browser: AuroraTestBrowser,
    health_registration: Registration,
):
    """
    Verify that submitting the form with an invalid enumerator code
    and without giving consent triggers the correct validation errors.
    """
    cache.clear()
    browser.open(health_registration.get_absolute_url())
    formsets_qs = health_registration.flex_form.formsets.filter(enabled=True).order_by("ordering")
    all_formset_titles = [fs.title for fs in formsets_qs]

    assert len(all_formset_titles) >= 2, (
        f"Expected at least 2 enabled formsets with titles for health_registration, "
        f"but found {len(all_formset_titles)}. Titles found: {all_formset_titles}"
    )

    def verify_formset_title_visibility(title, index):
        selector = f"div[data-msgid='{title}']"
        assert browser.is_element_present(selector), (
            f"FormSet title container for '{title}' (selector: '{selector}') not found in the DOM."
        )
        assert browser.is_element_visible(selector), (
            f"FormSet title container for '{title}' '{selector}' found in the DOM but is not visible."
        )

    verify_formset_title_visibility(all_formset_titles[0], 0)
    verify_formset_title_visibility(all_formset_titles[1], 1)

    enumerator_code_name = "intro-and-consent-0-enumerator_code"
    enumerator_code_selector = f"input[name='{enumerator_code_name}']"
    browser.assert_element_present(enumerator_code_selector)
    browser.type(enumerator_code_selector, "INVALIDCODE")

    who_to_register_name = "intro-and-consent-0-who_to_register"
    who_to_register_selector = f"input[name='{who_to_register_name}'][value='myself']"
    browser.assert_element_present(who_to_register_selector)
    browser.click(who_to_register_selector)

    consent_checkbox_name = "intro-and-consent-0-consent_h_c"
    admin_fields = [
        ("id_household-info-0-admin1_h_c", "Abia", "State"),
        ("id_household-info-0-admin2_h_c", "Aba North", "LGA"),
        ("id_household-info-0-admin3_h_c", "Ariaria", "Ward"),
    ]

    for field_id, text_to_select, field_type in admin_fields:
        select2_container_selector = f"#{field_id}"
        try:
            browser.assert_element_present(select2_container_selector)
            browser.select2_select(field_id, text_to_select)
            browser.sleep(1)
        except Exception as e:
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

    submit_button_selector = "//input[@type='submit' and @data-msgid='Save']"
    browser.assert_element_present(submit_button_selector, by="xpath")
    browser.click(submit_button_selector, by="xpath")

    enumerator_error_message = "Enter a valid value"
    enumerator_error_selector = f"#id_{enumerator_code_name}_error"
    try:
        browser.wait_for_element_visible(enumerator_error_selector, timeout=10)
        browser.assert_text(enumerator_error_message, selector=enumerator_error_selector)
    except TimeoutException:
        pytest.fail(f"Validation error '{enumerator_error_message}' for enumerator code not found or not visible.")

    consent_error_message = "This field is required."
    consent_error_selector = f"#id_{consent_checkbox_name}_error"
    try:
        browser.wait_for_element_visible(consent_error_selector, timeout=10)
        browser.assert_text(consent_error_message, selector=consent_error_selector)
    except TimeoutException:
        pytest.fail(f"Validation error '{consent_error_message}' for consent checkbox not found or not visible.")
