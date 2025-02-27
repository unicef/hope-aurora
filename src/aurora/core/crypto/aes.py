from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad


class AESCrypto:
    def __init__(self, key=None):
        self.key = key or get_random_bytes(16)

    def encrypt(self, data):
        cipher = AES.new(self.key, AES.MODE_CBC)  # Using CBC mode
        # Pad the data to be multiple of block size (16 bytes for AES)
        padded_data = pad(data.encode(), AES.block_size)
        ciphertext = cipher.encrypt(padded_data)
        return cipher.iv, ciphertext  # Return IV along with ciphertext for decryption

    def decrypt(self, iv, ciphertext):
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decrypted_data = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return decrypted_data.decode()
