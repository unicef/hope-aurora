import json

import pytest
from Crypto.PublicKey import RSA

from aurora.core.crypto import RSACrypto, crypt, decrypt

LANGUAGES = {
    "english": "first",
    "ukrainian": "АаБбВвГгҐґДдЕеЄєЖжЗзИиІіЇїЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЬьЮюЯя",
    "chinese": "姓名",
    "japanese": "ファーストネーム",
    "arabic": "الاسم الأول",
    "BIG": "АаБбВвГгҐґДдЕеЄєЖжЗзИиІіЇїЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЬьЮюЯя" * 1024,
}

PUBLIC = b"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxPyACSP38j/kB9jR8QPZ
dPch3L+27c7FmzPOnA2FAI52Cfn6aiddQQyEyN6b3pXHxN+3haVIPr2yYu+4gwBC
YoUm45sMtXXtpAmQXjQoXGNGvNMsYQPWd10MHC1eSMXrxAGzqKZaTLcbrY06FIyt
nWc24+D8tHj50QEoSbIk5ex+8gtZAXi0YWmQWma4+IbpiE353wqjjvSDtyHQxnZ/
emWBBlsTJnovkD3uPLkRlQE4dIqYkLvBgRFCZm88aGBjsQXWd2goJbpfQXmatCdh
IAlFN8Uvk+muYvmHroIxVNoz496WLSfFT8f1Dr0b6+urUT2dF20Rk7M+iFm4F2wB
MQIDAQAB
-----END PUBLIC KEY-----"""

PRIVATE = b"""-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEAxPyACSP38j/kB9jR8QPZdPch3L+27c7FmzPOnA2FAI52Cfn6
aiddQQyEyN6b3pXHxN+3haVIPr2yYu+4gwBCYoUm45sMtXXtpAmQXjQoXGNGvNMs
YQPWd10MHC1eSMXrxAGzqKZaTLcbrY06FIytnWc24+D8tHj50QEoSbIk5ex+8gtZ
AXi0YWmQWma4+IbpiE353wqjjvSDtyHQxnZ/emWBBlsTJnovkD3uPLkRlQE4dIqY
kLvBgRFCZm88aGBjsQXWd2goJbpfQXmatCdhIAlFN8Uvk+muYvmHroIxVNoz496W
LSfFT8f1Dr0b6+urUT2dF20Rk7M+iFm4F2wBMQIDAQABAoIBAAFAGQ/1yn0fKrNi
DPMasyaq6uwby213AooZqhYTf+ShAt7NV2mVFmJzUeR0hUjEaqA1S1Tt16eOTLOU
EffC6Kj3b2fCdDIyrW99IA15B0iO2MQaEw4KmDHpxUnof9C2cOitmhZX9/rErshL
PTMkMXXuUcrggroiinNpLnhJSTKsasPpMiwbypERyCl4LLBJ6T0QTyAH06CCgppM
68W6qAC5yV32OjULTDGzvdMYsFtFT0bUXRv5O09H52xMmYQneglElsdHvH4eKpA4
mquL7mX1YjnUKJ49cT/PHThlXN3Dy5gWzzrYmrewGerASw2X7VcEBzZSDp7JDLyA
T3OrQAECgYEAyemXvtxAQG+dPTsGyDnq6K55rJc9lppw1qSrroTOR06oXCrNWfDJ
0mBSqZf7cVwJZYPj1k9qCjmSJiy9p98AVx3/VtzPjJLUJwriVmhSonMQpAz1D3i2
F6F4b3EYj2VPBFAGEh8g3WT/PNv48v+9JdmA5p/u6EdXD1oIXT2fq5ECgYEA+cEX
PkQDHULQfW3v19gWI/F+CCX8B9My/c3U27Pa2I0ZZQMwFLwlwX66VCC7gD9Ty3hB
35YIT5RJwQX8xU2v7pPfFdaWSTO5fiDzBqo67r5WDfWnPCsqDpnlYmM1Kdtxu/TU
Awk0toGqMYUZNBG7fEWqHGfxRlF8eojAJyvT66ECgYALX+l4ixfjiWYmSOj85qZh
LVMVcf+6OEEbFnPFhR3JzpiVeKPQ6Uu1Wk/N1g4IONMesOto61hh8xRUqjiU+G8g
eUQlNJNMrAjfmjFeBMqC9FB/rWswz/ASLLqILKrhiSeGaqus4awMTOBEIXBI4Ddb
poEofOIMm9g/uSa3ef1AwQKBgAcI71SrqcLLPQArdpQH3CfLB5fHKiA2TLtlbtd5
a3KqFssHmfUbj5yxqyHvghiMsBmNG53mpflH3gP33TTZiVkZBTGiR71sHY918iJ/
7QUIi3f9MWa6eIbMwu9QiBDTw5JdxRMI0VlKsbaPXzReQ3+unqoKK3ulk/IHpBH2
ZBPBAoGANeGueLzJ/laKVvJ3fnkKTPw/japz/+GKyWGCjEIBSj5ucF2ktnBUA2xF
tzDrltIzCujyRRDKDIqdxOTOC/WzR+UJKz/W4MWq4ttTwvH2QiDPBsUUB7GhiMbB
btcA1UFpS9TFL++uMmwbcMzykITUTxhHp0QWEg1cpj8HFakPBZ4=
-----END RSA PRIVATE KEY-----"""


@pytest.fixture()
def registration(simple_form):
    from testutils.factories import RegistrationFactory

    reg = RegistrationFactory()
    priv, pub = reg.setup_encryption_keys()
    reg._private_pem = priv
    return reg


@pytest.fixture(scope="session")
def key():
    return RSA.generate(2048)


@pytest.fixture(scope="session")
def private_pem(key) -> str:
    return key.export_key().decode()


@pytest.fixture(scope="session")
def public_pem(key) -> str:
    return key.publickey().export_key().decode()


@pytest.mark.parametrize("data", LANGUAGES.values(), ids=LANGUAGES.keys())
def test_crypt(data, public_pem, private_pem):
    encrypted = crypt(data, public_pem)
    assert isinstance(encrypted, bytes)
    assert decrypt(encrypted, private_pem) == data


@pytest.mark.parametrize("data", [LANGUAGES], ids=["json"])
def test_crypt_complex(data, public_pem, private_pem):
    dumped = json.dumps(data)
    encrypted = crypt(dumped, public_pem)
    decrypted = decrypt(encrypted, private_pem)
    assert decrypted == dumped
    assert json.loads(decrypted) == data


@pytest.mark.parametrize("data", [LANGUAGES], ids=["json"])
def test_crypt_field(data, registration):
    from aurora.registration.models import Record

    record: Record = registration.add_record(data)
    decrypted = record.decrypt(registration._private_pem)
    assert decrypted == data


def test_crypter1():
    c = RSACrypto()
    assert c.decrypt(c.crypt("AAAA")) == "AAAA"


def test_crypter2():
    c = RSACrypto(PUBLIC.decode(), PRIVATE.decode())
    assert c.decrypt(c.crypt("AAAA")) == "AAAA"
