from unittest.mock import Mock

import pytest
from django import forms
from testutils.selenium import AuroraTestBrowser

from aurora.core.fields import CompilationTimeField, MultiCheckboxField, SmartFileField, LocationField
from aurora.registration.models import Record
from aurora.core.models import Validator

pytestmark = pytest.mark.selenium


@pytest.fixture
def mock_state():
    from django.contrib.auth.models import AnonymousUser

    from aurora.state import state

    state.request = Mock(user=AnonymousUser())
    yield
    state.request = None


@pytest.fixture
def czech_form():
    from aurora.core.cache import cache
    cache.clear()

    v1, __ = Validator.objects.update_or_create(
        label="length_1_50",
        defaults={
            "active": True,
            "target": Validator.FIELD,
            "code": "value.length>1 && value.length<=50 ? true: 'String size 1 to 50'",
        },
    )
    v2, __ = Validator.objects.update_or_create(
        label="email_validator",
        defaults={
            "active": True,
            "target": Validator.FIELD,
            "code": "value.includes('@') ? true : 'Invalid email format'",
        }
    )
    from testutils.factories import FormFactory, FormSetFactory

    frm = FormFactory(name="CzechForm")
    frm.fields.get_or_create(label="time", defaults={"field_type": CompilationTimeField})
    frm.fields.get_or_create(label="Příjmení", defaults={"field_type": forms.CharField, "required": True})
    frm.fields.get_or_create(label="Jméno", defaults={"field_type": forms.CharField, "required": True})
    frm.fields.get_or_create(
        label="Rodné číslo",
        defaults={
            "field_type": forms.CharField,
            "required": True,
            "validator": v1,
            "advanced": {"smart": {"index": 1}},
        },
    )
    frm.fields.get_or_create(label="Město", defaults={"field_type": forms.CharField, "required": True})
    frm.fields.get_or_create(label="Telefonní číslo", defaults={"field_type": forms.CharField, "required": False})
    frm.fields.get_or_create(label="Datum narození", defaults={"field_type": forms.DateField, "required": False})
    frm.fields.get_or_create(label="E-mail", defaults={"field_type": forms.EmailField, "required": False, "validator": v2})
    frm.fields.get_or_create(
        label="Pohlaví",
        defaults={
            "field_type": forms.ChoiceField,
            "required": False,
            "choices": (("", "---------"), ("m", "Muž"), ("ž", "Žena")),
        },
    )
    frm.fields.get_or_create(label="Souhlas se zpracováním údajů", defaults={"field_type": forms.BooleanField, "required": True})
    frm.fields.get_or_create(label="Lokace", defaults={"field_type": LocationField, "required": False})

    address_form = FormFactory(name="AddressForm")
    address_form.fields.get_or_create(label="Typ adresy", defaults={"field_type": forms.CharField, "required": True}) # Address type
    address_form.fields.get_or_create(label="Ulice a číslo", defaults={"field_type": forms.CharField, "required": True}) # Street and number
    address_form.fields.get_or_create(label="PSČ", defaults={"field_type": forms.CharField, "required": True})  # Postal code
    FormSetFactory(parent=frm, flex_form=address_form, name="addresses")

    frm.fields.get_or_create(
        label="Zájmy",
        defaults={
            "field_type": MultiCheckboxField,
            "required": False,
            "choices": (("sport", "Sport"), ("hudba", "Hudba"), ("umění", "Umění"), ("cestování", "Cestování")),
        },
    )
    return frm


@pytest.fixture
def czech_registration(czech_form):
    from testutils.factories import RegistrationFactory

    return RegistrationFactory(
        name="registration czech #1",
        flex_form=czech_form,
        encrypt_data=False,
        unique_field_path="rodné_číslo",
        unique_field_error="Rodné číslo is not unique",
    )


def test_register(mock_state, browser: AuroraTestBrowser, czech_registration):
    url = czech_registration.get_absolute_url()
    browser.open(url)

    browser.type("input[name=příjmení]", "Novák")
    browser.type("input[name=jméno]", "Jan")
    browser.type("input[name=rodné_číslo]", "123456/7890")
    browser.type("input[name=město]", "Praha")
    browser.type("input[name=telefonní_číslo]", "+420123456789")
    browser.type("input[name=datum_narození]", "1980-12-24")
    browser.type("input[name=e_mail]", "jan.novak@example.cz")
    browser.choose("select[name=pohlaví]", "m")
    browser.check("input[name=souhlas_se_zpracováním_údajů]")
    browser.type("input[name=lokace]", "50.0755, 14.4378")

    browser.click("a:contains('Add another AddressForm')")
    browser.type("input[name=addresses-0-typ_adresy]", "Trvalé bydliště")
    browser.type("input[name=addresses-0-ulice_a_číslo]", "Hlavní 123/4")
    browser.type("input[name=addresses-0-psč]", "11000")

    browser.click("a:contains('Add another AddressForm')")
    browser.type("input[name=addresses-1-typ_adresy]", "Přechodné bydliště")
    browser.type("input[name=addresses-1-ulice_a_číslo]", "Vedlejší 456/7")
    browser.type("input[name=addresses-1-psč]", "22000")

    browser.check("input[name=zájmy][value=sport]")
    browser.check("input[name=zájmy][value=hudba]")

    browser.click("input[name=_save_form]")
    reg_id = browser.get_text("#registration-id")
    browser.click("a:contains('register another household')")
    assert Record.objects.filter(id=reg_id.split("/")[1])
