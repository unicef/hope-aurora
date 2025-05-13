from unittest.mock import MagicMock, Mock

from aurora.ddt_panels import StatePanel


def test_state_panel():
    panel = StatePanel(Mock(), MagicMock())
    assert panel.nav_title()
    assert panel.enabled
    assert panel.title()
    assert panel.url() == ""
    assert panel.content
