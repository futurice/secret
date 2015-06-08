# Secret

Manage secrets.

Secret provides a Python 3.4+ interface for a secure solution to store secrets backed by Amazon services:
notably IAM for access policies, KMS for encryption keys and S3 for storage.

## Setup

* `pip install secret`
* Login to Amazon AWS: https://console.aws.amazon.com/iam/home
* In IAM, create a (KMS) Encryption Key called 'secret'
 * Check that Region Filter is set to the region S3 will use
* In S3, create a bucket called 'secret'
 * Enable Versioning, and set a Lifecycle policy

Use ~/.boto, ~/.aws/credentials profiles (http://boto.readthedocs.org/en/latest/boto_config_tut.html):
```$ AWS_PROFILE=profile secret```

or ENV variables:
```
export AWS_ACCESS_KEY_ID=
export AWS_SECRET_ACCESS_KEY=
export AWS_SESSION_TOKEN=
export AWS_DEFAULT_REGION=
$ secret
```

## Usage

Initialize a new project (configuration stored in .secret). The used vault corresponds to S3 bucket name:
```
$ secret setup --vault secret --project helloworld
```

Commands:
```
$ secret list
$ secret put hello world
$ secret put ssh_key ~/.ssh/id_rsa
$ secret get ssh_key
$ secret config
$ secret delete ssh_key
$ secret versions
$ secret versions ssh_key
$ secret get ssh_key --version <version>
$ secret envs
$ secret put hello world --env production
$ secret config --env production
```
