from setuptools import setup, find_packages, Command

import os, sys, subprocess

class TestCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        if os.getenv('PYTHON_VERSION') == 'secret-python3':# .travis.yml
            subprocess.call(['bash conv_py2_to_py3.bash',], shell=True)

        raise SystemExit(
            subprocess.call(['py.test',]))

install_requires=['boto3>=0.0.18', 'pycryptodome>=3.1','tabulate>=0.7.5','pytest>=2.8.5', 'six']
if sys.version_info.major == 2:
    install_requires.append('trollius>=1.0.4')

setup(
    name="secret",
    version='0.6.11',
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
    install_requires=install_requires,
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
