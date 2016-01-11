from setuptools import setup, find_packages, Command

import os, sys, subprocess

class TestCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        raise SystemExit(
            subprocess.call(['py.test',]))

setup(
    name='secret',
    version='0.6.0',
    description='Secret is for storing secrets. Backed by Amazon Web Services: IAM for access policies, KMS for encryption keys and S3 for storage',
    keywords = 'secret secrets project vault aws amazon cloud',
    author = 'Jussi Vaihia',
    author_email = 'jussi.vaihia@futurice.com',
    license='Apache2',
    url='https://github.com/futurice/secret',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
    ],
    install_requires=['boto3>=0.0.18', 'pycryptodome>=3.1','trollius>=1.0.4','tabulate>=0.7.5','pytest>=2.8.5'],
    packages = ["secret"],
    include_package_data = True,
    cmdclass = {
        'test': TestCommand,
    },
    entry_points={
        'console_scripts': [
            'secret = secret.secret:runner'
            ]
        }
)
