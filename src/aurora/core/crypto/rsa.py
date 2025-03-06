import base64
import io
import logging
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

BLOCK_SIZE = 16
CHUNK_SIZE = BLOCK_SIZE * 1024 * 1024 + BLOCK_SIZE
TAG_SIZE = BLOCK_SIZE
CIPHERTXT_SIZE = CHUNK_SIZE - TAG_SIZE
NONCE_SIZE = BLOCK_SIZE

logger = logging.getLogger(__name__)


def crypt(data: str, public_pem: str) -> bytes:
    data = data.encode("utf-8")
    file_out = io.BytesIO()
    file_in = io.BytesIO(data)

    public_key = serialization.load_pem_public_key(public_pem.encode(), backend=default_backend())
    symmetric_key = os.urandom(32)
    enc_symmetric_key = public_key.encrypt(
        symmetric_key, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    file_out.write(enc_symmetric_key)

    while True:
        data_chunk = file_in.read(1024)
        if data_chunk:
            iv = os.urandom(16)
            cipher = Cipher(algorithms.AES(symmetric_key), modes.GCM(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(data_chunk) + encryptor.finalize()
            file_out.write(iv + encryptor.tag + ciphertext)
        else:
            break

    file_out.seek(0)
    return file_out.read()


def decrypt(data: bytes, private_pem: str):
    file_in = io.BytesIO(data)
    file_out = io.BytesIO()

    private_key = serialization.load_pem_private_key(private_pem.encode(), password=None, backend=default_backend())
    enc_key_size = private_key.key_size // 8
    enc_symmetric_key = file_in.read(enc_key_size)
    symmetric_key = private_key.decrypt(
        enc_symmetric_key,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )

    while True:
        iv = file_in.read(16)
        if not iv:
            break
        tag = file_in.read(16)
        ciphertxt_tag = file_in.read(1024)
        cipher = Cipher(algorithms.AES(symmetric_key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        file_out.write(decryptor.update(ciphertxt_tag) + decryptor.finalize())

    file_out.seek(0)
    return file_out.read().decode()


def decrypt_offline(data: str, private_pem: str) -> bytes:
    encrypted_symmetric_key = data[:344]
    form_fields = data[344:]

    private_key = serialization.load_pem_private_key(private_pem.encode(), password=None, backend=default_backend())
    decrypted_symmetric_key = private_key.decrypt(
        base64.b64decode(encrypted_symmetric_key),
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )

    enc = base64.b64decode(form_fields)
    cipher = Cipher(
        algorithms.AES(decrypted_symmetric_key), modes.CBC(decrypted_symmetric_key[:16]), backend=default_backend()
    )
    decrypter = cipher.decryptor()
    decrypted_data = decrypter.update(enc) + decrypter.finalize()

    unpadder = PKCS7(128).unpadder()
    return unpadder.update(decrypted_data) + unpadder.finalize()
