from __future__ import absolute_import
import os, sys, json
import trollius as asyncio
from trollius import From, Return

from secret.vault import Kms

BOTO_DEFAULT = ''
ENCODING = 'utf-8'

class Storage:
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
        if not key: raise Return("Key name missing")
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
