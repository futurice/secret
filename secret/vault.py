from __future__ import absolute_import
from base64 import b64encode, b64decode
from secret.algo import AesEax

ENCODING = 'utf-8'

def tob64(value):
    return b64encode(value).decode(ENCODING)

class Vault:
    def encrypt(self, value, **kw): pass
    def decrypt(self, value, **kw): pass

class KmsDataKey:
    def __init__(self, vault, key, ciphertext=None, num_bytes=64):
        if ciphertext:
            res = vault.client.decrypt(CiphertextBlob=ciphertext)
            self.wrapped_key = ciphertext
        else:
            res = vault.client.generate_data_key(KeyId=key, NumberOfBytes=num_bytes)
            self.wrapped_key = res['CiphertextBlob']
        self.data_key = res['Plaintext'][:32]
        self.hmac_key = res['Plaintext'][32:]

class Kms(Vault):
    def __init__(self, session, key="alias/secret"):
        self.client = session.client('kms')
        self.key = key
        self.cipher = AesEax

    def keyclass(self, **kw):
        return KmsDataKey(vault=self, key=self.key, **kw)

    def encrypt(self, value, **kw):
        datakey = self.keyclass()

        cipher = self.cipher(datakey.data_key)
        c_text, nonce, tag = cipher.encrypt(value)

        hmac = cipher.hmac(datakey.hmac_key, c_text)

        data = {}
        data['key'] = tob64(datakey.wrapped_key)
        data['contents'] = tob64(c_text)
        data['nonce'] = tob64(nonce)
        data['tag'] = tob64(tag)
        data['hmac'] = hmac
        data['is_file'] = kw.get('is_file', False)
        data['is_binary'] = kw.get('is_binary', False)
        return data

    def decrypt(self, data, **kw):
        datakey = self.keyclass(ciphertext=b64decode(data['key']))

        cipher = self.cipher(datakey.data_key)
        assert (cipher.hmac(datakey.hmac_key, b64decode(data['contents'])) == data['hmac'])

        return cipher.decrypt(b64decode(data['contents']),
                nonce=b64decode(data['nonce']),
                tag=b64decode(data['tag']),)
