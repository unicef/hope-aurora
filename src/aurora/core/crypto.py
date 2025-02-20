import base64
import io
import json
import logging

from django.conf import settings

from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import unpad
from cryptography.fernet import Fernet

from aurora.core.utils import safe_json

BLOCK_SIZE = 16
CHUNK_SIZE = BLOCK_SIZE * 1024 * 1024 + BLOCK_SIZE
TAG_SIZE = BLOCK_SIZE
CIPHERTXT_SIZE = CHUNK_SIZE - TAG_SIZE
NONCE_SIZE = BLOCK_SIZE

logger = logging.getLogger(__name__)


class Crypto:
    def __init__(self, key=None):
        self.key = key or settings.FERNET_KEY

    def encrypt(self, v):
        try:
            if isinstance(v, str):
                value = v
            else:
                value = safe_json(v)

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


class RSACrypto:
    def __init__(self, public_pem: str = None, private_pem: str = None):
        if public_pem and private_pem:
            pass
        else:
            key = RSA.generate(2048)
            private_pem = key.export_key().decode()
            public_pem = key.publickey().export_key().decode()

        if not isinstance(public_pem, str) or not isinstance(private_pem, str):
            raise BaseException("Public and private key need to be string")
        self.public_pem = public_pem.encode()
        self.private_pem = private_pem.encode()

    def crypt(self, data):
        return crypt(data, self.public_pem)

    def decrypt(self, data):
        return decrypt(data, self.private_pem)


def get_public_keys(pem):
    public_key = PKCS1_OAEP.new(RSA.import_key(pem))
    symmetric_key = b"12345678901234567890123456789012"
    enc_symmetric_key = public_key.encrypt(symmetric_key)
    return symmetric_key, enc_symmetric_key


def crypt(data: str, public_pem: bytes) -> bytes:
    data = data.encode("utf-8")
    file_out = io.BytesIO()
    file_in = io.BytesIO(data)
    symmetric_key, enc_symmetric_key = get_public_keys(public_pem)
    file_out.write(enc_symmetric_key)
    while True:
        data_chunk = file_in.read(CIPHERTXT_SIZE)
        if data_chunk:
            cipher = AES.new(symmetric_key, AES.MODE_GCM)
            file_out.write(cipher.nonce + b"".join(reversed(cipher.encrypt_and_digest(data_chunk))))
        else:
            break
    file_out.seek(0)
    return file_out.read()


def decrypt(data: bytes, private_pem: bytes):
    file_in = io.BytesIO(data)
    file_in.seek(0)
    file_out = io.BytesIO()
    key = RSA.import_key(private_pem)
    private_key = PKCS1_OAEP.new(key)
    enc_key_size = key.size_in_bytes()
    symmetric_key = private_key.decrypt(file_in.read(enc_key_size))
    nonce = file_in.read(NONCE_SIZE)
    while nonce:
        ciphertxt_tag = file_in.read(CHUNK_SIZE)
        cipher = AES.new(symmetric_key, AES.MODE_GCM, nonce)
        file_out.write(cipher.decrypt_and_verify(ciphertxt_tag[BLOCK_SIZE:], ciphertxt_tag[:BLOCK_SIZE]))
        nonce = file_in.read(NONCE_SIZE)

    file_out.seek(0)
    return file_out.read().decode()


def decrypt_offline(data: str, private_pem: bytes) -> str | bytes:
    encrypted_symmetric_key = data[:344]
    form_fields = data[344:]

    key = RSA.importKey(private_pem)
    cipher = PKCS1_OAEP.new(key, hashAlgo=SHA256)
    decrypted_symmetric_key = json.loads(cipher.decrypt(base64.b64decode(encrypted_symmetric_key)))
    enc = base64.b64decode(form_fields)

    derived_key = base64.b64decode("LefjQ2pEXmiy/nNZvEJ43i8hJuaAnzbA1Cbn1hOuAgA=")
    cipher = AES.new(derived_key, AES.MODE_CBC, decrypted_symmetric_key.encode("utf-8"))

    return unpad(cipher.decrypt(enc), 16)
