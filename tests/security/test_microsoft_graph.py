from pathlib import Path
from unittest import mock

import pytest
from requests import HTTPError

from aurora.security.microsoft_graph import MicrosoftGraphAPI, MicrosoftGraphAPIError

# Note in case cassettes need to be refreshed
#  See. https://github.com/getsentry/responses?tab=readme-ov-file#record-responses-to-files


@pytest.fixture
def api():
    return MicrosoftGraphAPI()


@pytest.mark.file_path(Path(__file__).parent / "api.yaml")
def test_api(file_mocked_responses, api):
    api.get_token()


def test_api_no_key(mocked_responses, settings):
    settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY = ""
    api = MicrosoftGraphAPI()
    with pytest.raises(Exception, match=r"Configure AZURE_CLIENT_KEY and/or AZURE_CLIENT_SECRET"):
        api.get_token()


def test_api_fail(mocked_responses, api):
    mocked_responses.add(mocked_responses.POST, "https://login.microsoftonline.com/unicef.org/oauth2/token", status=401)
    with pytest.raises(Exception, match=r"Unable to fetch token from Azure.*"):
        api.get_token()


@pytest.mark.file_path(Path(__file__).parent / "get_results_not_found.yaml")
def test_get_results_email_not_found(file_mocked_responses, api):
    with pytest.raises(Exception, match=r"User not found"):
        api.get_user_data(email="invalid@example.com")


@pytest.mark.file_path(Path(__file__).parent / "get_results_id_not_found.yaml")
def test_get_results_id_not_found(file_mocked_responses, api):
    with pytest.raises(Exception, match=r"404 Client Error: "):
        api.get_user_data(uuid="abc")


@pytest.mark.file_path(Path(__file__).parent / "get_results.yaml")
def test_get_user_data_email(file_mocked_responses, api):
    api.get_user_data(email="saxix@unicef.org")


@pytest.mark.file_path(Path(__file__).parent / "user_data_uuid.yaml")
def test_get_user_data_uuid(file_mocked_responses, api):
    api.get_user_data(uuid="21d2ecba-83e4-4e81-a93c-d44f55dd222e")


@pytest.mark.file_path(Path(__file__).parent / "get_results_401.yaml")
def test_get_results_401(file_mocked_responses, api):
    with mock.patch("aurora.security.microsoft_graph.Response.raise_for_status", side_effect=HTTPError):
        with pytest.raises(HTTPError):
            api.get_user_data(email="saxix@unicef.org")


def test_get_results_unknown(mocked_responses, api):
    with mock.patch("aurora.security.microsoft_graph.Response.raise_for_status", side_effect=HTTPError):
        with pytest.raises(MicrosoftGraphAPIError, match=r"You must provide 'uuid' or 'email' argument."):
            api.get_user_data()
