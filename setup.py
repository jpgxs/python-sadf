#!/usr/bin/env python
# coding: utf-8

import codecs
import re
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def get_version():
    return re.search(
        r"""__version__\s+=\s+(?P<quote>['"])(?P<version>.+?)(?P=quote)""",
        open('sadf/__init__.py').read()
    ).group('version')


setup(
    name='sadf',
    version=get_version(),
    author='Joshua Griffiths',
    author_email='jgriffiths@ceramyq.com',
    url='http://github.com/jpgxs/python-sadf',
    description='Parse sysstat (sa/sar) output into Pandas Dataframes',
    long_description=codecs.open('README.rst', encoding='utf-8').read(),
    install_requires=[
        'dateparser>=0.4.0',
        'pandas>=0.18.0',
        'pytz',
        'six>=1.0.0',
        'tzlocal>=1.0.0',
    ],
    packages=['sadf'],
    platforms=['POSIX'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.0",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5"
    ]
)
