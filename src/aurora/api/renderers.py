import json
import logging
from collections.abc import Mapping
from typing import Any

from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from rest_framework.renderers import BaseRenderer

logger = logging.getLogger(__name__)

ENCRYPTED_MEDIA_TYPE = "application/encrypted+json"


class EncryptedJSONRenderer(BaseRenderer):
    """
    DRF renderer that Fernet-encrypts the full JSON response payload.

    Activated via DRF content-type negotiation when the client sends:
        Accept: application/encrypted+json

    Requires ``AURORA_PAYLOAD_ENCRYPTION_KEY`` to be set in Django settings.
    The encrypted wire format is a JSON object with a single ``payload`` field:
        {"payload": "<fernet_token>"}

    The token is a URL-safe base64-encoded Fernet ciphertext that the consumer
    must decrypt using the same pre-shared key.
    """

    media_type = ENCRYPTED_MEDIA_TYPE
    format = "encrypted_json"
    charset = None

    def render(
        self,
        data: Any,
        accepted_media_type: str | None = None,
        renderer_context: Mapping[str, Any] | None = None,
    ) -> bytes:
        key: str = getattr(settings, "AURORA_PAYLOAD_ENCRYPTION_KEY", "")
        if not key:
            raise ImproperlyConfigured(
                "AURORA_PAYLOAD_ENCRYPTION_KEY must be configured to serve encrypted API responses. "
                "Generate a key with: "
                'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
            )
        json_bytes = json.dumps(data).encode("utf-8")
        token: bytes = Fernet(key).encrypt(json_bytes)
        return json.dumps({"payload": token.decode("utf-8")}).encode("utf-8")
