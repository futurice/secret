# Secret
[![Build Status](https://travis-ci.org/futurice/secret.svg?branch=master)](https://travis-ci.org/futurice/secret)

Secret is for storing secrets. Backed by Amazon Web Services:
notably IAM for access policies, KMS for encryption keys and S3 for storage.

## Setup

* `pip install secret`
 * Python3 version available as `secret-python3`.
* Login to Amazon AWS: https://console.aws.amazon.com/iam/home
* In IAM, create a (KMS) Encryption Key called 'secret'
 * Check that Region Filter is set to the region S3 will use
* In S3, create a bucket called 'secret'
 * Enable Versioning, and set a Lifecycle policy

Configure AWS credentials for Boto (http://boto.readthedocs.org/en/latest/boto_config_tut.html).

## Usage

Add global configuration to `~/.secret/credentials`, for example:
```bash
[default]
# vault=S3 bucket name
# vaultkey=KMS encryption key handle
vault=secret
vaultkey=alias/secret
region=eu-central-1
```

Add any configuration overrides in .secret, eg. `{"project":"my-only-project"}` to not need to specify `-P my-only-project`.

## Commands

```bash
$ secret
<CLI instructions>

$ secret list
(empty)

$ secret put hello world
Success! Wrote: secret/default/hello

$ secret list
hello

$ secret get hello
world

$ secret put ssh_key ~/.ssh/id_rsa
Success! Wrote: secret/default/ssh_key

$ secret get ssh_key -o ~/.ssh/id_rsa
```

### Keyspace

Project configuration (defined in .secret) allows for addressing keys with a shorthand syntax. The full naming
is also available.  That is, `project`/`environment`/`key` lookups like `helloworld/default/hello` equal `default/hello` equal `hello`.
The `/` character is reserved for supporting nested keys.

### Grouping

By namespacing keys it is possible to create groups of interest. Nested key names can be up to 1024 ASCII characters long.

```
$ secret put postgres/username joe
$ secret put postgres/password joespassword
$ secret put postgres/timeout 3600
$ secret get postgres
Key       Value
timeout   3600
password  joespassword
username  joe
```

### Versioning

With S3 versioning enabled all changes leave an audit trail:

```bash
$ secret versions
<list all versions of all keys>

$ secret versions ssh_key
<list versions of a single key>

$ secret delete ssh_key
Success! Deleted: helloworld/default/ssh_key

$ secret get ssh_key
<NoSuchKey>

$ secret get ssh_key --version <version>
(key value data)
```

### Environments

By default all project keys are stored under ```default``` environment. To store user/situation specific values
for the same keys (and new ones), provide ```--env``` while issuing operations.

```bash
$ secret envs
$ secret put hello world --env production
$ secret get --env production
```

### Debugging

To enable verbose output for commands use ```--debug 1``` argument.

### Development

Setup a local development environment for Secret:
```
virtualenv py2venv --python=python2
source py2venv/bin/activate
pip install -r requirements.txt
pip install pytest
mkdir -p ~/.secret/credentials
echo """
[default]
vault=secret
vaultkey=alias/secret
region=eu-central-1
""" > $HOME/.secret/credentials
export AWS_PROFILE=default
```

Client usage:
```
./venvcmd ls
```

Run tests:
```
py.test
```
