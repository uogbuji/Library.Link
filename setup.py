#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Highly recommend installing using `pip install -U .` not `python setup.py install`

Uses pkgutil-style namespace package (Working on figuring out PEP 420)

Note: careful not to conflate install_requires with requirements.txt

https://packaging.python.org/discussions/install-requires-vs-requirements/

Reluctantly use setuptools for now to get install_requires & long_description_content_type
'''

import sys
from setuptools import setup
#from distutils.core import setup

PROJECT_NAME = 'librarylink'
PROJECT_DESCRIPTION = 'Tools for working with Library.Link',
PROJECT_LICENSE = 'License :: OSI Approved :: Apache Software License'
PROJECT_AUTHOR = 'Uche Ogbuji'
PROJECT_AUTHOR_EMAIL = 'uche@ogbuji.net'
PROJECT_MAINTAINER = 'Zepheira'
PROJECT_MAINTAINER_EMAIL = 'uche@zepheira.com'
PROJECT_URL = 'http://zepheira.com/'
PACKAGE_DIR = {'librarylink': 'pylib'}
PACKAGES = ['librarylink', 'librarylink.crawler']
SCRIPTS = [
    'exec/liblink_resource_summary',
    'exec/liblink_crawl',
    'exec/liblink_title_report',
    'exec/liblinklist',
]

CORE_REQUIREMENTS = [
    'amara3.xml',
    'versa',
    'html5lib',
    'rdflib',
    'aiohttp',
    'aiohttp-cache',
    'pybibframe',
    'markdown',
    'isbn_hyphenate',
]

# From http://pypi.python.org/pypi?%3Aaction=list_classifiers
CLASSIFIERS = [
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Development Status :: 3 - Alpha",
    #"Environment :: Other Environment",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Operating System :: OS Independent",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Internet :: WWW/HTTP",
]

KEYWORDS=['xml', 'web', 'data']

version_file = 'pylib/version.py'
exec(compile(open(version_file, "rb").read(), version_file, 'exec'), globals(), locals())
__version__ = '.'.join(version_info)

LONGDESC = '''Library.Link
Tools for processing data from the Library.Link project

Uche Ogbuji < uche@ogbuji.net >

# Install

Requires Python 3.5+

    pip install LibraryLink

# liblink_resource_summary

Command Tool to parse RDFa 1.1 Lite (from the Library.Link pages or other HTML). Example:

    liblink_resource_summary "http://link.houstonlibrary.org/portal/Half-of-a-yellow-sun-Chimamanda-Ngozi/n7KqqbZFJuM/"
'''

LONGDESC_CTYPE = 'text/markdown'

setup(
    name=PROJECT_NAME,
    version=__version__,
    description=PROJECT_DESCRIPTION,
    license=PROJECT_LICENSE,
    author=PROJECT_AUTHOR,
    author_email=PROJECT_AUTHOR_EMAIL,
    maintainer=PROJECT_MAINTAINER,
    maintainer_email=PROJECT_MAINTAINER_EMAIL,
    url=PROJECT_URL,
    package_dir=PACKAGE_DIR,
    packages=PACKAGES,
    scripts=SCRIPTS,
    install_requires=CORE_REQUIREMENTS,
    classifiers=CLASSIFIERS,
    long_description=LONGDESC,
    long_description_content_type=LONGDESC_CTYPE,
    keywords=KEYWORDS,
)
