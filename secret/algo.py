from Crypto.Cipher import AES
from Crypto.Hash.HMAC import HMAC
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes

class Cipher:
    def encrypt(self, value, **kw): pass
    def decrypt(self, value, **kw): pass

class AesEax(Cipher):
    def __init__(self, key):
        self.key = key

    def cipher(self, nonce):
        return AES.new(self.key, AES.MODE_EAX, nonce=nonce)

    @classmethod
    def hmac(self, key, msg):
        return HMAC(key, msg=msg, digestmod=SHA256).hexdigest()

    def encrypt(self, value):
        nonce = get_random_bytes(16)
        c_text, tag = self.cipher(nonce).encrypt_and_digest(value)
        return c_text, nonce, tag

    def decrypt(self, value, nonce, tag):
        return self.cipher(nonce).decrypt_and_verify(value, tag)
