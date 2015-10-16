from __future__ import absolute_import
from botocore.exceptions import ClientError
import os, sys, json
import trollius as asyncio
from trollius import From, Return
from collections import OrderedDict

from secret.vault import Kms

BOTO_DEFAULT = ''
ENCODING = 'utf-8'

class Storage(object):
    def list(self, **kw): pass
    def get(self, key, **kw): pass
    def put(self, key, value, **kw): pass

class S3(Storage):
    def __init__(self, session, vault, vaultkey, project, env='default'):
        self.client = session.client('s3')
        self.bucket = vault
        self.vaultkey = vaultkey
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
        if not all([vault, project]):
            sys.exit("Vault and/or project undefined")
        try:
            result = yield From(self.get(project))
            res = "Project with this name already exists"
        except:
            result = yield From(self.put(project, ''))
            self.project.save(dict(vault=vault, project=project, key=self.vaultkey))
            res = "Success! Project created. Configuration stored in %s"%self.project.name
        raise Return(res)

    @asyncio.coroutine
    def list_backend(self, prefix=None, **kw):
        if not prefix:
            prefix = self.prefix + self.env
        raise Return(self.client.list_objects(Bucket=self.bucket, Prefix=prefix, MaxKeys=1000, Delimiter=kw.get('delimiter', BOTO_DEFAULT)))

    @asyncio.coroutine
    def list(self, key=None, **kw):
        key = self.prefixify(key)
        response = yield From(self.list_backend(prefix=key, **kw))
        raise Return([self.prefixify(k['Key'], reverse=True) for k in response.get('Contents', [])])

    @asyncio.coroutine
    def config(self, key=None, **kw):
        contents = yield From(self.list_backend(prefix=self.prefixify(key)))
        contents = contents.get('Contents', [])
        tasks = [self.get(key=obj['Key'], **kw) for obj in contents]
        results = yield From(asyncio.gather(*tasks))
        keys = [k['Key'].split('/')[-1] for k in contents]
        raise Return(OrderedDict(zip(keys, results)))

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
        else:
            raise Return(result)

    @asyncio.coroutine
    def get_backend(self, **kw):
        raise Return(self.client.get_object(**kw))

    @asyncio.coroutine
    def get(self, key, **kw):
        key = self.prefixify(key or '')
        extra = {}
        if kw.get('version'):
            extra['VersionId'] = kw.get('version')
        try:
            result = yield From(self.get_backend(Bucket=self.bucket, Key=key, **extra))
        except Exception as e:
            if not kw.get('in_group_check'):
                # check for grouped keys
                key = key.rstrip('/')+'/'
                kw['in_group_check'] = True
                result = yield From(self.config(key=key, **kw))
                if not result:
                    result = "Error! The specified key does not exist."
                raise Return(result)
            raise
        raise Return(self.vault.decrypt(json.loads(result['Body'].read().decode(ENCODING))).decode(ENCODING))

    @asyncio.coroutine
    def delete_backend(self, **kw):
        raise Return(self.client.delete_object(**kw))

    @asyncio.coroutine
    def delete(self, key, **kw):
        key = self.prefixify(key)
        result = yield From(self.delete_backend(Bucket=self.bucket, Key=key))
        if result.get('ResponseMetadata').get('HTTPStatusCode') == 204:
            raise Return("Success! Deleted: %s"%key)
        else:
            raise Return(result)

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
        elif key is not None:
            if self.prefix not in key and self.env not in key:
                key = '{}{}{}'.format(self.prefix, self.env, key)
            elif self.prefix not in key:
                key = '{}{}'.format(self.prefix, key)
        return key
