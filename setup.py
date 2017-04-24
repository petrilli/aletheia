#!/usr/bin/env python
from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Click>=6.0',
    'google-api-python-client>=1.6',
    'six>=1.10',
]

test_requirements = [
    'pytest>=3.0',
    'pytest-mock>=1.6',
]

setup(
    name='aletheia',
    version='0.1.0',
    description="Manage secrets in Google Cloud Platform",
    long_description=readme + '\n\n' + history,
    author="Christopher Petrilli",
    author_email='petrilli@amber.org',
    url='https://github.com/petrilli/aletheia',
    packages=[
        'aletheia',
    ],
    package_dir={
        'aletheia': 'aletheia',
    },
    entry_points={
        'console_scripts': [
            'aletheia=aletheia.cli:main',
        ],
    },
    include_package_data=True,
    install_requires=requirements,
    license="BSD license",
    zip_safe=False,
    keywords='aletheia',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements,
)
