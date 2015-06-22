#!/usr/bin/env python
from __future__ import absolute_import
import argparse
import os, sys
import json

from secret.project import Project

ENCODING = 'utf-8'
DATAFILE = '.secret'
BOTO_DEFAULT = ''
ALIASES = {'ls':'list',}

args = None
project = None

if sys.version_info.major == 2:
    import logging
    os.environ['TROLLIUSDEBUG'] = "1" # more informative tracebacks
    logging.basicConfig(level=logging.CRITICAL)

def print_status(args):
    aws_profile = bool(os.getenv("AWS_PROFILE"))
    aws_key = bool(os.getenv('AWS_ACCESS_KEY_ID'))
    aws_secret = bool(os.getenv('AWS_SECRET_ACCESS_KEY'))
    print("VAULT: {} PROJECT: {} ENV: {} AWS/profile: {} AWS/key: {} AWS/secret: {}"\
            .format(args.vault, args.project, args.env, aws_profile, aws_key, aws_secret))

def prepare():
    global args, project
    p = argparse.ArgumentParser()
    p.add_argument("action")
    p.add_argument("key", nargs="?", default=None)
    p.add_argument("value", nargs="?", default=None)
    p.add_argument("--version", default=None)
    p.add_argument("--region", help="AWS region", default="us-east-1")
    p.add_argument("--vaultkey", help="Name of KMS key", default="alias/secret")
    p.add_argument("--vault", help="Name of vault (eg. S3 bucket)", default="secret")
    p.add_argument("--project", help="Name of project (eg. S3 'folder')", default=None)
    p.add_argument("--env", help="Environment namespace for keys", default='default')
    p.add_argument("--datafile", default=DATAFILE)
    p.add_argument("--debug", default=None)
    args = p.parse_args()
    args.action = ALIASES.get(args.action, args.action)

    project = Project(name=args.datafile)

    if args.action != 'setup':
        args.vault = project.load().get('vault')
        args.project = project.load().get('project')
        assert all([args.vault, args.project])

    if args.action == 'help':
        print_status(args)
        sys.exit("1. Run setup 2. Check that AWS environment variables for profile OR key+secret are set")

if __name__ == '__main__':
    """ Basic actions before imports for a responsive CLI """
    prepare()

from collections import Iterable

from pprint import pprint as pp
from base64 import b64encode, b64decode
import boto3

import six
import trollius as asyncio
from trollius import From, Return

from Crypto.Cipher import AES
from Crypto.Hash.HMAC import HMAC
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes

class Storage:
    def list(self, **kw): pass
    def get(self, key, **kw): pass
    def put(self, key, value, **kw): pass

class S3(Storage):
    def __init__(self, session, vault, vaultkey, project, env='default'):
        self.client = session.client('s3')
        self.bucket = vault
        self.vault = Kms(session=session, key=vaultkey)
        self.project = project
        self.prefix = self.project.load().get('project', '')
        self.env = env + '/'
        if self.prefix:
            self.prefix += '/'

    @asyncio.coroutine
    def create_bucket(self, name=None, **kw):
        # administrator creates bucket for projects
        name = name or self.bucket
        result = self.client.create_bucket(Bucket=name)
        raise Return(result)

    @asyncio.coroutine
    def setup(self, vault, project, **kw):
        # project-user creates a folder inside bucket
        try:
            assert all([vault, project])
        except AssertionError as e:
            sys.exit("Missing arguments for setup, eg: $ secret setup --vault secret --project helloworld")
        try:
            result = yield From(self.get(project))
            res = "Project with this name already exists"
        except:
            result = yield From(self.put(project, ''))
            self.project.save(dict(vault=vault, project=project))
            res = "Saved settings to %s"%self.project.name
        raise Return(res)

    @asyncio.coroutine
    def list_backend(self, prefix=None, **kw):
        if not prefix:
            prefix = self.prefix + self.env
        raise Return(self.client.list_objects(Bucket=self.bucket, Prefix=prefix, MaxKeys=1000, Delimiter=kw.get('delimiter', BOTO_DEFAULT)))

    @asyncio.coroutine
    def list(self, prefix=None, **kw):
        response = yield From(self.list_backend(prefix=prefix, **kw))
        raise Return([self.prefixify(k['Key'], reverse=True) for k in response.get('Contents', [])])

    @asyncio.coroutine
    def config(self, **kw):
        contents = yield From(self.list_backend())
        contents = contents.get('Contents', [])
        tasks = [self.get(obj['Key']) for obj in contents]
        results = yield From(asyncio.gather(*tasks))
        raise Return(dict(zip([self.prefixify(k['Key'], reverse=True) for k in contents], results)))

    @asyncio.coroutine
    def put_backend(self, **kw):
        raise Return(self.client.put_object(**kw))

    @asyncio.coroutine
    def put(self, key, value, **kw):
        key = self.prefixify(key)
        if os.path.isfile(value):
            value = open(os.path.expandvars(os.path.expanduser(value)), 'r').read()
        data = self.vault.encrypt(value.encode(ENCODING))
        data['name'] = key
        result = yield From(self.put_backend(Bucket=self.bucket, Key=key, Body=json.dumps(data)))
        if result.get('ResponseMetadata').get('HTTPStatusCode') == 200:
            raise Return("Success! Wrote: %s"%key)

    @asyncio.coroutine
    def get(self, key, **kw):
        key = self.prefixify(key)
        extra = {}
        if kw.get('version'):
            extra['VersionId'] = kw.get('version')
        res = self.client.get_object(Bucket=self.bucket, Key=key, **extra)
        raise Return(self.vault.decrypt(json.loads(res['Body'].read().decode(ENCODING))).decode(ENCODING))

    @asyncio.coroutine
    def delete(self, key, **kw):
        key = self.prefixify(key)
        raise Return(self.client.delete_object(Bucket=self.bucket, Key=key))

    @asyncio.coroutine
    def versions(self, **kw):
        prefix = kw.get('prefix', self.prefix)
        response = self.client.list_object_versions(Bucket=self.bucket, Prefix=self.prefix)
        versions = []
        for k in response.get('Versions', []):
            key = self.prefixify(k['Key'], reverse=True)
            if kw.get('key') and kw.get('key')!=key: continue
            versions.append(dict(key=key, version=k['VersionId'], is_latest=k['IsLatest'], modified=k['LastModified']))
        raise Return(versions)

    @asyncio.coroutine
    def envs(self, **kw):
        contents = yield From(self.list_backend(prefix=self.prefix, delimiter='/'))
        raise Return(list(k['Prefix'].split('/')[1] for k in contents.get('CommonPrefixes', [])))

    def prefixify(self, key, reverse=False):
        if reverse:
            key = key.replace('{}{}'.format(self.prefix, self.env), '')
        elif self.prefix not in key:
            key = '{}{}{}'.format(self.prefix, self.env, key)
        return key

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

def tob64(value):
    return b64encode(value).decode(ENCODING)

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
        return data

    def decrypt(self, data, **kw):
        datakey = self.keyclass(ciphertext=b64decode(data['key']))

        cipher = self.cipher(datakey.data_key)
        assert (cipher.hmac(datakey.hmac_key, b64decode(data['contents'])) == data['hmac'])

        return cipher.decrypt(b64decode(data['contents']),
                nonce=b64decode(data['nonce']),
                tag=b64decode(data['tag']),)

@asyncio.coroutine
def main():
    global args, project
    region = os.getenv("AWS_DEFAULT_REGION", args.region)
    kw = {}
    if not os.getenv("AWS_PROFILE"):
        kw = dict(aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.getenv('AWS_SESSION_TOKEN'),)

    if args.debug:
        boto3.set_stream_logger(name='botocore')

    session = boto3.session.Session(region_name=region, **kw)
    storage = S3(session=session, vault=args.vault, vaultkey=args.vaultkey, env=args.env, project=project)

    method = getattr(storage, args.action)
    result = yield From(method(**vars(args)))
    def is_str(result):
        try:
            return isinstance(result, basestring)
        except NameError:
            return isinstance(result, str)
    if any(isinstance(result, k) for k in [list]):
        pp(result)
    elif is_str(result):
        print(result)
    else:
        for k,v in six.iteritems(result):
            print(k,'=',v)

def runner():
    global args
    if not args: prepare()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

if __name__ == '__main__':
    runner()
