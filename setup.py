from setuptools import setup, find_packages

setup(
    name='secret',
    version='0.4.4',
    description='Secret is a Python library for storing secrets. Backed by Amazon Web Services: IAM for access policies, KMS for encryption keys and S3 for storage',
    keywords = 'secret secrets project vault aws amazon cloud',
    author = 'Jussi Vaihia',
    author_email = 'jussi.vaihia@futurice.com',
    license='Apache2',
    url='https://github.com/futurice/secret',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
    ],
    install_requires=['boto3>=0.0.18', 'pycryptodome>=3.1','trollius>=1.0.4'],
    packages = ["secret"],
    include_package_data = True,
    entry_points={
        'console_scripts': [
            'secret = secret.secret:runner'
            ]
        }
)
