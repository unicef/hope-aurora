from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By


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
                raise MaxParentsReached()
    raise NoSuchElementException()


def parent_element(obj, up=1):
    return obj.find_elements(By.XPATH, f".{'/..' * up}")
