import logging
from typing import Any

import requests
from django.conf import settings
from django.http import Http404
from requests import Response

logger = logging.getLogger(__name__)

DJANGO_USER_MAP = {
    "username": "mail",
    "email": "mail",
    "first_name": "givenName",
    "last_name": "surname",
    "ad_uuid": "id",
}


class MicrosoftGraphAPIError(Exception):
    pass


class MicrosoftGraphAPI:
    def __init__(self) -> None:
        self.azure_client_id = settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY
        self.azure_client_secret = settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET

    def get_token(self) -> str:
        if not self.azure_client_id or not self.azure_client_secret:
            raise MicrosoftGraphAPIError("Configure AZURE_CLIENT_KEY and/or AZURE_CLIENT_SECRET")

        post_dict = {
            "grant_type": "client_credentials",
            "client_id": self.azure_client_id,
            "client_secret": self.azure_client_secret,
            "resource": settings.AZURE_GRAPH_API_BASE_URL,
        }
        response = requests.post(settings.AZURE_TOKEN_URL, post_dict, timeout=60)

        if response.status_code != 200:
            logger.error(f"Unable to fetch token from Azure. {response.status_code} {response.content.decode('utf-8')}")
            raise MicrosoftGraphAPIError("Unable to fetch token from Azure.")

        json_response = response.json()
        return json_response["access_token"]

    def _get_results(self, url: str) -> dict:
        headers = {"Authorization": f"Bearer {self.get_token()}"}
        response: Response = requests.get(url, headers=headers, timeout=60)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.exception(e)
            raise
        return response.json()

    def get_user_data(self, *, email: str | None = None, uuid: str | None = None) -> Any:
        try:
            if uuid:
                q = f"{settings.SOCIAL_AUTH_RESOURCE}/v1.0/users/{uuid}"
                value = self._get_results(q)
            elif email:
                q = (
                    f"{settings.SOCIAL_AUTH_RESOURCE}/v1.0/users/?"
                    f"$filter=userType in ['Member','guest'] and mail eq '{email}'"
                )
                data = self._get_results(q)
                value = data["value"][0]
            else:
                logger.error("You must provide 'uuid' or 'email' argument.")
                raise MicrosoftGraphAPIError("You must provide 'uuid' or 'email' argument.")
        except IndexError as e:
            logger.error(f"User not found using email={email},uuid={uuid}")
            raise Http404("User not found") from e
        return value
