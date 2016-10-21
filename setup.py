from distutils.core import setup

setup(
    name = 'librarylink',
    version = '0.2',
    description = 'Tools for working with Library.Link',
    license = 'License :: OSI Approved :: Apache Software License',
    author = 'Uche Ogbuji',
    author_email = 'uche@zepheira.com',
    url = 'http://zepheira.com/',
    package_dir={'librarylink': 'lib'},
    packages = ['librarylink'],
    scripts=['exec/parse_rdfa',],
    #http://packages.python.org/distribute/setuptools.html#declaring-dependencies
#    install_requires = ['amara == 2', 'versa'],
)
