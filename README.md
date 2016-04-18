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

Start by creating a new project: ```--vault``` is the S3 bucket name,
```--vaultkey``` the KMS key and ```--project``` a destination "folder" (created for you) in the S3 bucket:
```
$ secret setup --vault secret --vaultkey alias/secret --region us-east-1 --project helloworld
```
The project configuration is stored in .secret to avoid typing required arguments on every command.

Global configuration can be stored to `~/.secret/credentials`, for example:
```bash
[default]
vault=secret
vaultkey=alias/secret
```

## Commands

```bash
$ secret
<CLI instructions>

$ secret list


$ secret put hello world
Success! Wrote: secret/default/hello

$ secret list
hello

$ secret get hello
world

$ secret put ssh_key ~/.ssh/id_rsa
Success! Wrote: secret/default/ssh_key
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

