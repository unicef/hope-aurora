from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from seleniumbase import BaseCase


class MaxParentsReached(NoSuchElementException):
    pass


def find_relative(obj, selector_type, path, max_parents=3):
    """Tries to find a SINGLE element with a common ancestor"""
    for c in range(max_parents, 0, -1):
        try:
            elems = obj.find_elements(selector_type, f"./{'../' * c}/{path}")
            if len(elems) == 1:
                return elems[0]
        except Exception:
            if max_parents == c:
                raise MaxParentsReached() from None
    raise NoSuchElementException()


def parent_element(obj, up=1):
    return obj.find_elements(By.XPATH, f".{'/..' * up}")


class AuroraSeleniumTC(BaseCase):
    live_server_url: str = ""

    def setUp(self, masterqa_mode=False):
        super().setUp()
        from testutils.factories import SuperUserFactory

        super().setUpClass()
        self.admin_user = SuperUserFactory()
        self.admin_user._password = "password"

    def tearDown(self):
        self.save_teardown_screenshot()
        super().tearDown()
        self.admin_user.delete()

    def base_method(self):
        pass

    def open(self, url: str):
        self.maximize_window()
        return super().open(f"{self.live_server_url}{url}")

    def select2_select(self, element_id: str, value: str):
        self.slow_click(f"span[aria-labelledby=select2-{element_id}-container]")
        self.wait_for_element_visible("input.select2-search__field")
        self.click(f"li.select2-results__option:contains('{value}')")
        self.wait_for_element_absent("input.select2-search__field")

    def login(self):
        self.open("/admin/")
        if self.get_current_url() == f"{self.live_server_url}/admin/login/?next=/admin/":
            self.type("input[name=username]", f"{self.admin_user.username}")
            self.type("input[name=password]", f"{self.admin_user._password}")
            self.submit('input[value="Log in"]')
            self.wait_for_ready_state_complete()


AuroraTestBrowser = AuroraSeleniumTC
