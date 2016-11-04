from distutils.core import setup
import sys, os

versionfile = 'lib/version.py'
exec(compile(open(versionfile, "rb").read(), versionfile, 'exec'), globals(), locals())
__version__ = '.'.join(version_info)

LONGDESC = '''Library.Link
==========

Tools for processing data from the Library.Link project

`Uche Ogbuji`_ < uche@ogbuji.net >

Install
-------

Requires:

-  Python 3.4+
-  `amara3-xml`_ package
-  `html5lib`_ package
-  `pytest`_ (for running the test suite)

For the latter 3, you can do:

pip install pytest amara3-xml html5lib

parse_rdfa
----------

Command Tool to parse RDFa 1.1 Lite (from the Library.Link pages or other HTML). Example:

::

    parse_rdfa --rdfttl=foo.ttl "http://link.houstonlibrary.org/portal/Half-of-a-yellow-sun-Chimamanda-Ngozi/n7KqqbZFJuM/"
'''


setup(
    name = 'librarylink',
    version = __version__,
    description = 'Tools for working with Library.Link',
    license = 'License :: OSI Approved :: Apache Software License',
    author = 'Uche Ogbuji',
    author_email = 'uche@zepheira.com',
    url = 'http://zepheira.com/',
    package_dir={'librarylink': 'lib'},
    packages = ['librarylink'],
    scripts=['exec/parse_rdfa',],
    classifiers = [ # From http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 3 - Alpha",
        #"Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
    ],
    #long_description = LONGDESC,
    #http://packages.python.org/distribute/setuptools.html#declaring-dependencies
#    install_requires = ['amara == 2', 'versa'],
)
