import base64

from aurora.core.crypto.symmetric import Symmetric


def test_symmetric():
    key = base64.urlsafe_b64encode(b"a" * 32)
    c = Symmetric(key).encrypt("ABC")
    assert Symmetric(key).decrypt(c) == "ABC"
