from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from seleniumbase import BaseCase
from testutils.factories import FormFactory, RegistrationFactory, SuperUserFactory

from aurora.core.models import FlexForm, FlexFormField
from aurora.registration.models import Registration

BaseCase.main(__name__, __file__)  # Call pytest


class AuroraSeleniumTC(StaticLiveServerTestCase, BaseCase):
    def open(self, url: str):
        return super().open(f"{self.live_server_url}{url}")

    def select2_select(self, element_id: str, value: str):
        self.slow_click(f"span[aria-labelledby=select2-{element_id}-container]")
        self.wait_for_element_visible("input.select2-search__field")
        self.click(f"li.select2-results__option:contains('{value}')")
        self.wait_for_element_absent("input.select2-search__field")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.registration: "Registration" = RegistrationFactory()
        cls.form: "FlexForm" = FormFactory()
        cls.admin_user = SuperUserFactory()
        cls.admin_user._password = "password"

    @classmethod
    def tearDownClass(cls):
        FlexForm.objects.all().delete()
        FlexFormField.objects.all().delete()
        Registration.objects.all().delete()

    def setUp(self, masterqa_mode=False):
        super().setUp(masterqa_mode)
        self.open("/admin/")
        if self.get_current_url() == f"{self.live_server_url}/admin/login/?next=/admin/":
            self.type("input[name=username]", f"{self.admin_user.username}")
            self.type("input[name=password]", f"{self.admin_user._password}")
            self.submit('input[value="Log in"]')
            self.wait_for_ready_state_complete()


class CreateOrganization(AuroraSeleniumTC):
    def test_add_organization(self):
        self.click_link("Organizations")
        self.click('a:contains("Add organization")')
        self.type("input[name=name]", "UNICEF")
        self.submit('input[value="Save"]')


class CreateForm(AuroraSeleniumTC):
    def test_add_form(self):
        self.click_link("Flex Forms")
        self.click('a:contains("Add Flex Form")')
        self.select2_select("id_project", self.registration.project.name)
        self.type("input#id_name", "Form-Test")
        self.click('input[name="_save"]')
        self.open_if_not_url("/admin/")
        self.wait_for_ready_state_complete()
        assert FlexForm.objects.filter(name="Form-Test").exists()


class CreateField(AuroraSeleniumTC):
    def test_add_field(self):
        self.click_link("Flex Fields")
        self.click('a:contains("Add Flex Field")')
        self.select2_select("id_flex_form", self.form.name)
        self.type("input#id_label", "FlexField-Test")
        self.click('input[name="_save"]')
        self.open_if_not_url("/admin/")
        self.wait_for_ready_state_complete()
        assert FlexFormField.objects.filter(label="FlexField-Test").exists()
