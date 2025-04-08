import pytest
from testutils.factories import ValidatorFactory

from aurora.core.models import Validator


@pytest.fixture
def birth_after_1900(db):
    code = """
    var limit1 = Date.parse("1900-01-01");
    var today = new Date();
    var dt = Date.parse(value);
    if (dt < limit1)
        "the date should be after 1900";
    else
        if (dt > today)
            "the date should be before today";
        else
            true
    """
    return ValidatorFactory(name="birth_after_1900", target=Validator.FIELD, active=True, code=code)
