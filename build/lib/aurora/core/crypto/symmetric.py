import base64
import logging
from typing import Any

from cryptography.fernet import Fernet
from django.conf import settings

from aurora.core.utils import safe_json

logger = logging.getLogger(__name__)


class Symmetric:
    def __init__(self, key=None):
        self.key = key or settings.FERNET_KEY

    def encrypt(self, v: "str|dict[str, Any]") -> str:
        if isinstance(v, str):
            value = v
        else:
            value = safe_json(v)
        try:
            cipher_suite = Fernet(self.key)  # key should be byte
            encrypted_text = cipher_suite.encrypt(value.encode("ascii"))
            return base64.urlsafe_b64encode(encrypted_text).decode("ascii")
        except Exception as e:
            logger.exception(e)
        return value

    def decrypt(self, value):
        try:
            txt = base64.urlsafe_b64decode(value)
            cipher_suite = Fernet(self.key)
            return cipher_suite.decrypt(txt).decode("ascii")
        except Exception as e:
            logger.exception(e)
        return value
