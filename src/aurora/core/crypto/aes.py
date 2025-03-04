from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import base64


class AESCrypto:
    def __init__(self, hex_key=None):
        self.key = bytes(hex_key.encode()) if hex_key else get_random_bytes(16)

    def encrypt(self, plaintext):
        padded_plaintext = pad(plaintext, AES.block_size)
        cipher = AES.new(self.key, AES.MODE_ECB)
        ciphertext = cipher.encrypt(padded_plaintext)
        return base64.b64encode(ciphertext).decode("utf-8")

    def decrypt(self, ciphertext_base64):
        decipher = AES.new(self.key, AES.MODE_ECB)
        decrypted = decipher.decrypt(base64.b64decode(ciphertext_base64))
        original_plaintext = unpad(decrypted, AES.block_size)
        return original_plaintext.decode()
