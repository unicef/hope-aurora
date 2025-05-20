from unittest.mock import Mock

import pytest

from contextlib import nullcontext as does_not_raise
from aurora.core.bitcaster import BitcasterEventManager, BitcasterEvents


@pytest.fixture
def mock_bitcaster_sdk(monkeypatch):
    """Mock bitcaster_sdk to avoid sending events"""
    mock_bitcaster = Mock()
    mock_bitcaster.trigger = Mock()
    mock_bitcaster.init = Mock()

    monkeypatch.setattr("aurora.core.bitcaster.bitcaster_sdk", mock_bitcaster)
    return mock_bitcaster


@pytest.fixture
def bitcaster_manager(mock_bitcaster_sdk) -> BitcasterEventManager:
    """Return a BitcasterEventManager instance for testing"""
    return BitcasterEventManager("test_project", "test_application")


@pytest.mark.parametrize(
    "event, context, expectation",
    [
        (BitcasterEvents.USER_REGISTERED, {}, pytest.raises(ValueError, match="Missing context keys")),
        (BitcasterEvents.USER_REGISTERED, {"user": "Mario"}, does_not_raise()),
        (BitcasterEvents.GENERATE_PASSWORD, {"user": "Mario"}, pytest.raises(ValueError, match="Missing context keys")),
    ],
    ids=["empty_context", "valid_context", "missing_email"],
)
def test_check_context_with_ids(event, context, expectation, bitcaster_manager):
    """Test context validation for different events and contexts"""
    with expectation:
        bitcaster_manager.check_context(event, context)


def test_check_context_unknown_event(monkeypatch, bitcaster_manager):
    """Test context validation for an unknown event"""
    original_context = bitcaster_manager.CONTEXT.copy()
    context_no_user_registered = original_context.copy()
    context_no_user_registered.pop(BitcasterEvents.USER_REGISTERED)

    monkeypatch.setattr(BitcasterEventManager, "CONTEXT", context_no_user_registered)

    with pytest.raises(ValueError, match="Unknown event"):
        bitcaster_manager.check_context(BitcasterEvents.USER_REGISTERED, {"user": "testuser"})


def test_trigger_event(bitcaster_manager, mock_bitcaster_sdk):
    """Test that the trigger method correctly calls the SDK"""
    context = {"user": "Mario"}
    bitcaster_manager.trigger(BitcasterEvents.USER_REGISTERED, context)
    mock_bitcaster_sdk.trigger.assert_called_once_with(
        "test_project", "test_application", BitcasterEvents.USER_REGISTERED.value, context=context, options=None
    )
