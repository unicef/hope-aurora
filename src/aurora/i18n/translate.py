import logging

import uuid

import requests
from abc import ABC, abstractmethod
from django.conf import settings

logger = logging.getLogger(__name__)


class Translator(ABC):
    @abstractmethod
    def translate(self, language, text):
        ...


class AzureTranslator:
    endpoint = "https://api.cognitive.microsofttranslator.com/translate"

    def __init__(self) -> None:
        super().__init__()

        self.headers = {
            "Ocp-Apim-Subscription-Key": settings.AZURE_TRANSLATOR_KEY,
            "Ocp-Apim-Subscription-Region": settings.AZURE_TRANSLATOR_LOCATION,
            "Content-type": "application/json",
            "X-ClientTraceId": str(uuid.uuid4()),
        }

    def translate(self, language, text):
        try:
            body = [{"text": text}]
            params = {"api-version": "3.0", "from": "en", "to": [language]}
            request = requests.post(self.endpoint, params=params, headers=self.headers, json=body)
            response = request.json()
            return response[0]["translations"][0]["text"]
        except Exception as e:
            logger.exception(e)
        return ""
