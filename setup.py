from distutils.core import setup

setup(
    name='Juju XaaS Client Binding',
    version='0.1.0',
    author='Justin SB',
    author_email='justin@fathomdb.com',
    packages=['jujuxaas'],
    url='http://pypi.python.org/pypi/JujuXaasClient/',
    license='LICENSE.txt',
    description='Client library for Juju XaaS.',
    long_description=open('README.md').read(),
    install_requires=[
        'requests'
    ],
)