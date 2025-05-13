from typing import TYPE_CHECKING

import pytest

from aurora.registration.strategies import (
    DisplayTestStrategy,
    SaveAndDisplayTestStrategy,
    SaveToDB,
    TransactionTestStrategy,
)

if TYPE_CHECKING:
    from aurora.registration.models import Registration


@pytest.fixture
def registration(db) -> "Registration":
    from testutils.factories import RegistrationFactory

    return RegistrationFactory(
        name="registration #3",
        encrypt_data=False,
        export_allowed=True,
        unique_field_path="last_name",
        unique_field_error="last_name is not unique",
    )


def test_save_to_db(registration):
    s = SaveToDB(registration)
    assert s.save({})

    registration.encrypt_data = True
    s = SaveToDB(registration)
    assert s.save({})


def test_transactionteststrategy(registration):
    s = TransactionTestStrategy(registration)
    assert s.save({})


def test_saveanddisplayteststrategy(registration):
    s = SaveAndDisplayTestStrategy(registration)
    assert s.save({})


def test_displayteststrategy(registration):
    s = DisplayTestStrategy(registration)
    assert s.save({})
