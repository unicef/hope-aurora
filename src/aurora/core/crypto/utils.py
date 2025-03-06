import binascii

from constance import config


def get_x_auth_cred() -> bytes:
    return binascii.hexlify(config.UBA_CLIENT_NO.encode()).zfill(16)
