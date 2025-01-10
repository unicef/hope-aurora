import logging
from pathlib import Path

from django.core.management import call_command
from django.utils import translation

import pytest
from concurrency.api import disable_concurrency
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select

from aurora.i18n.gettext import gettext
from aurora.registration.models import Record


@pytest.fixture()
def data(db, settings):
    log = logging.getLogger("django.server")
    log.setLevel(logging.CRITICAL)
    with disable_concurrency():
        call_command("loaddata", Path(__file__).parent / "fixtures.json", verbosity=0)


LOCATIONS = {
    "uk-ua": ["Автономна Республіка Крим", "Бахчисарайський", "Ароматненська"],
    "en-us": ["Avtonomna Respublika Krym", "Bakhchysaraiskyi", "Aromatnenska"],
}


def pytest_generate_tests(metafunc):
    if "language" in metafunc.fixturenames:
        m = []
        ids = []
        for lang, __ in LOCATIONS.items():
            url = f"/{lang}/register/registration2/"
            #     return reverse("register", args=[registration.locale, registration.slug])
            m.append([lang, url])
            ids.append(lang)
        metafunc.parametrize("language,url", m, ids=ids)


@pytest.fixture(autouse=True)
def setup(selenium, data):
    selenium.implicitly_wait(3)
    dim = selenium.get_window_size()
    selenium.set_window_size(1100, dim["height"])


def set_locations(selenium, lang="uk-ua"):
    # LOCATIONS = ["Автономна Республіка Крим", "Бахчисарайський", "Ароматненська"]
    loc = LOCATIONS[lang]
    # ADMIN1
    selenium.find_by_css("fieldset.admin1_h_c .select2 .selection .select2-selection").click()
    selenium.wait_for(By.CSS_SELECTOR, ".select2-results__options .select2-results__option")
    selenium.find_by_css(".select2-search__field").send_keys(loc[0])
    selenium.wait_for(By.CSS_SELECTOR, ".select2-results__option--highlighted")
    selenium.find_by_css(".select2-search__field").send_keys(Keys.ENTER)

    # ADMIN2
    selenium.find_by_css("fieldset.admin2_h_c .select2 .selection .select2-selection").click()
    selenium.wait_for(By.CSS_SELECTOR, ".select2-results__options .select2-results__option")
    selenium.find_by_css(".select2-search__field").send_keys(loc[1])
    selenium.wait_for(By.CSS_SELECTOR, ".select2-results__option--highlighted")
    selenium.find_by_css(".select2-search__field").send_keys(Keys.ENTER)

    # ADMIN3
    selenium.find_by_css("fieldset.admin3_h_c .select2 .selection .select2-selection").click()
    selenium.wait_for(By.CSS_SELECTOR, ".select2-results__options .select2-results__option")
    selenium.find_by_css(".select2-search__field").send_keys(loc[2])
    selenium.wait_for(By.CSS_SELECTOR, ".select2-results__option--highlighted")
    selenium.find_by_css(".select2-search__field").send_keys(Keys.ENTER)


def individual(
    selenium,
    idx=0,
    role="head",
    collector=False,
    tax_id=None,
    passport=None,
    birth_date="2000-01-01",
    birth_certificate=None,
    birth_certificate_picture=None,
):
    selenium.find_by_css(f'input[name="individuals-{idx}-given_name_i_c"]').send_keys(f"Given Name #{idx}")
    selenium.find_by_css(f'input[name="individuals-{idx}-family_name_i_c"]').send_keys(f"Family Name #{idx}")
    selenium.find_by_css(f'input[name="individuals-{idx}-patronymic"]').send_keys(f"Patronymic #{idx}")
    selenium.find_by_css(f'input[name="individuals-{idx}-birth_date"]').send_keys(birth_date)
    selenium.find_by_css(f'input[name="individuals-{idx}-gender_i_c"]').click()

    if birth_certificate:
        selenium.find_by_css(f'input[name="individuals-{idx}-birth_certificate_no_i_c"]').send_keys(birth_certificate)

    if birth_certificate_picture:
        selenium.find_by_css(f'input[name="individuals-{idx}-birth_certificate_picture"]').send_keys(
            birth_certificate_picture
        )

    select = Select(selenium.find_element(By.CSS_SELECTOR, f'select[name="individuals-{idx}-relationship_i_c"]'))
    select.select_by_value(role)
    selenium.find_by_css(f'input[name="individuals-{idx}-phone_no_i_c"]').send_keys("0951234567")
    if collector:
        selenium.find_by_css(f'input[name="individuals-{idx}-role_i_c"][value="y"]').click()
        selenium.find_by_css(f'input[name="individuals-{idx}-bank_account_h_f"][value="y"]').click()
        select = Select(selenium.find_element(By.CSS_SELECTOR, f'select[name="individuals-{idx}-bank_name_h_f"]'))
        select.select_by_value("privatbank")

        selenium.find_by_css(f'input[name="individuals-{idx}-bank_account"]').send_keys("UA012345678901234567890123456")

        selenium.find_by_css(f'input[name="individuals-{idx}-bank_account_number"]').send_keys(
            "UA012345678901234567890123456"
        )
    else:
        selenium.find_by_css(f'input[name="individuals-{idx}-role_i_c"][value="n"]').click()
    selenium.find_by_css(f'input[name="individuals-{idx}-phone_no_i_c"]').send_keys("0951234567")
    if tax_id:
        selenium.wait_for(By.ID, f"question_id_individuals-{idx}-tax_id_no_i_c").click()
        selenium.find_by_css(f'input[name="individuals-{idx}-tax_id_no_i_c"]').send_keys(tax_id)
    if passport:
        # PASSPORT
        selenium.wait_for(By.ID, f"question_id_individuals-{idx}-national_id_no_i_c_1").click()
        selenium.find_by_css(f'input[name="individuals-{idx}-national_id_no_i_c_1"]').send_keys(passport)
    return idx


def fill_form(selenium, language):
    selenium.wait_for(By.CSS_SELECTOR, "label[for=id_household-0-residence_status_h_c_0]").click()
    set_locations(selenium, language)
    individual(selenium, 0, role="head", collector=True, tax_id="1234567890", passport="СЮ233889")


def submit(selenium):
    selenium.find_by_css('input[name="marketing-0-can_unicef_contact_you"][value="y"]').click()
    selenium.find_by_css('input[name="validator_uk-0-validation"]').click()
    selenium.find_by_css("input[type=submit]").click()


@pytest.mark.selenium
def test_ukr_base(live_server, selenium, language, url):
    selenium.get(f"{live_server.url}{url}")
    selenium.find_by_css("input[name=household-0-size_h_c").send_keys("4")

    birth_certificate_picture = str(Path(__file__).parent / "birth_certificate.png")
    fill_form(selenium, language)
    selenium.find_by_css(".formset.formset-individuals a.formset-add-button").click()
    individual(
        selenium,
        1,
        role="son_daughter",
        collector=False,
        birth_date="2022-06-01",
        birth_certificate="12345",
        birth_certificate_picture=birth_certificate_picture,
    )

    selenium.find_by_css(".formset.formset-individuals a.formset-add-button").click()
    individual(
        selenium,
        2,
        role="son_daughter",
        collector=False,
        birth_date="2022-06-01",
        birth_certificate="12345",
        birth_certificate_picture=birth_certificate_picture,
    )

    selenium.find_by_css(".formset.formset-individuals a.formset-add-button").click()
    individual(
        selenium,
        3,
        role="son_daughter",
        collector=False,
        birth_date="2022-06-01",
        birth_certificate="12345",
        birth_certificate_picture=birth_certificate_picture,
    )

    submit(selenium)
    #
    # HOPE-20220618-21
    registration_id = selenium.find_by_css("pre.registration-id").text
    parts, id = registration_id.split("/")
    prefix, date, dataset = parts.split("-")
    assert Record.objects.get(
        id=id,
        registration__id=dataset,
        unique_field="1234567890",
    )


@pytest.mark.selenium
def test_not_eligible(live_server, selenium, language, url):
    selenium.get(f"{live_server.url}{url}")
    fill_form(selenium, language)
    selenium.find_by_css("input[name=household-0-size_h_c").send_keys("4")
    birth_certificate_picture = str(Path(__file__).parent / "birth_certificate.png")

    selenium.find_by_css(".formset.formset-individuals a.formset-add-button").click()
    individual(
        selenium,
        1,
        role="son_daughter",
        collector=False,
        birth_date="2022-06-01",
        birth_certificate="12345",
        birth_certificate_picture=birth_certificate_picture,
    )

    selenium.find_by_css(".formset.formset-individuals a.formset-add-button").click()
    individual(
        selenium,
        2,
        role="son_daughter",
        collector=False,
        birth_date="2022-06-01",
        birth_certificate="12345",
        birth_certificate_picture=birth_certificate_picture,
    )

    selenium.find_by_css(".formset.formset-individuals a.formset-add-button").click()
    individual(selenium, 3, role="son_daughter", collector=False, birth_date="2000-06-01")

    submit(selenium)
    page = selenium.page_source
    with translation.override(language):
        assert gettext("please fix the errors below") in page
        assert (
            gettext("Your household information does not meet the " "eligibility criteria for UNICEF cash assistance")
            in page
        )


@pytest.mark.selenium
def test_size_mismatch(live_server, selenium, language, url):
    selenium.get(f"{live_server.url}{url}")
    fill_form(selenium, language)
    selenium.find_by_css("input[name=household-0-size_h_c").send_keys("6")
    birth_certificate_picture = str(Path(__file__).parent / "birth_certificate.png")

    selenium.find_by_css(".formset.formset-individuals a.formset-add-button").click()
    individual(
        selenium,
        1,
        role="son_daughter",
        collector=False,
        birth_date="2022-06-01",
        birth_certificate="12345",
        birth_certificate_picture=birth_certificate_picture,
    )

    selenium.find_by_css(".formset.formset-individuals a.formset-add-button").click()
    individual(
        selenium,
        2,
        role="son_daughter",
        collector=False,
        birth_date="2022-06-01",
        birth_certificate="12345",
        birth_certificate_picture=birth_certificate_picture,
    )

    submit(selenium)

    page = selenium.page_source

    with translation.override(language):
        size_mismatch = gettext("Household size and provided members do not match")
        assert gettext("please fix the errors below") in page
        assert size_mismatch in page
        # let double check
        # assert size_mismatch == "Розмір домогосподарства та надані члени не збігаються"


@pytest.mark.selenium
def test_birth_date_validation1(live_server, selenium, language, url):
    selenium.get(f"{live_server.url}{url}")
    selenium.find_by_css("input[name=household-0-size_h_c").send_keys("1")

    selenium.wait_for(By.CSS_SELECTOR, "label[for=id_household-0-residence_status_h_c_0]").click()
    set_locations(selenium, language)
    individual(selenium, 0, birth_date="2050-01-01")

    submit(selenium)
    page = selenium.page_source
    with translation.override(language):
        error_message = gettext("Date Of Birth cannot be in the future")
        assert gettext("please fix the errors below") in page
        assert error_message in page


@pytest.mark.selenium
def test_birth_date_validation2(live_server, selenium, language, url):
    # url = '/en-us/register/test1/'
    selenium.get(f"{live_server.url}{url}")

    selenium.find_by_css("input[name=household-0-size_h_c").send_keys("1")

    selenium.wait_for(By.CSS_SELECTOR, "label[for=id_household-0-residence_status_h_c_0]").click()
    set_locations(selenium, language)
    individual(selenium, 0, birth_date="1800-01-01")

    submit(selenium)
    page = selenium.page_source
    with translation.override(language):
        error_message = gettext("Date Of Birth seems too old")
        assert gettext("please fix the errors below") in page
        assert error_message in page


@pytest.mark.selenium
def test_only_one_head(live_server, selenium, language, url):
    # url = '/en-us/register/test1/'
    selenium.get(f"{live_server.url}{url}")

    selenium.find_by_css("input[name=household-0-size_h_c").send_keys("2")

    selenium.wait_for(By.CSS_SELECTOR, "label[for=id_household-0-residence_status_h_c_0]").click()
    set_locations(selenium, language)
    individual(selenium, 0, birth_date="2000-01-01", tax_id="1234567890")

    selenium.find_by_css(".formset.formset-individuals a.formset-add-button").click()
    individual(selenium, 1, birth_date="2000-01-01", tax_id="1234567890")

    submit(selenium)
    page = selenium.page_source
    with translation.override(language):
        error_message = gettext("Only one member can be set as Head Of Household")
        assert error_message in page


@pytest.mark.selenium
def test_one_collector(live_server, selenium, language, url):
    # url = '/en-us/register/test1/'
    selenium.get(f"{live_server.url}{url}")

    selenium.find_by_css("input[name=household-0-size_h_c").send_keys("2")

    selenium.wait_for(By.CSS_SELECTOR, "label[for=id_household-0-residence_status_h_c_0]").click()
    set_locations(selenium, language)
    individual(selenium, 0, birth_date="2000-01-01", tax_id="1234567890", role="head")

    submit(selenium)
    page = selenium.page_source
    with translation.override(language):
        error_message = gettext("At least one member must be set as 'Main Recipient'")
        assert error_message in page
