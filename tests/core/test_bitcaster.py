import sys
from unittest.mock import Mock

import pytest

from contextlib import nullcontext as does_not_raise

# Mock bitcaster_sdk at module level
mock_bitcaster_sdk = Mock()
mock_bitcaster_sdk.init = Mock()
mock_bitcaster_sdk.trigger = Mock()
mock_bitcaster_sdk.exceptions = type("MockExceptions", (), {"ConfigurationError": Exception})

sys.modules["bitcaster_sdk"] = mock_bitcaster_sdk

from aurora.core.bitcaster import BitcasterEventManager, BitcasterEvents


@pytest.fixture
def bitcaster_manager():
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
def test_check_context_with_ids(event, context, expectation):
    """Test context validation for different events and contexts"""
    with expectation:
        BitcasterEventManager.check_context(event, context)


def test_check_context_unknown_event(monkeypatch):
    """Test context validation for an unknown event"""
    original_context = BitcasterEventManager.CONTEXT.copy()
    context_copy = original_context.copy()
    context_copy.pop(BitcasterEvents.USER_REGISTERED)

    monkeypatch.setattr(BitcasterEventManager, "CONTEXT", context_copy)

    with pytest.raises(ValueError, match="Unknown event"):
        BitcasterEventManager.check_context(BitcasterEvents.USER_REGISTERED, {"user": "testuser"})


def test_trigger_event(bitcaster_manager):
    """Test that the trigger method correctly calls the SDK"""
    context = {"user": "Mario"}
    bitcaster_manager.trigger(BitcasterEvents.USER_REGISTERED, context)

    mock_bitcaster_sdk.trigger.assert_called_once_with(
        "test_project", "test_application", BitcasterEvents.USER_REGISTERED.value, context=context, options=None
    )
