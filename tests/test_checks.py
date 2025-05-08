from unittest.mock import Mock

from aurora.checks import check_azure_credentials


def test_check_azure_credentials() -> None:
    assert check_azure_credentials(Mock())
