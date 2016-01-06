# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from codecs import open
from os import path
import sys

here = path.abspath(path.dirname(__file__))
sys.path.insert(0, path.join(here,'lib'))

# Get the version from the VERSION file
with open(path.join(here, 'VERSION'), encoding='utf-8') as f:
    version = f.read()

SHORTDESC='Simple tiled (or untiled if desired) raster calculations (AKA "map algebra")'

LONGDESC='''This package enables simple tiled (or untiled if desired) raster calculations
(AKA "map algebra") from the commandline or from within your python scripts.
There is a commandline raster calculator and a raster calculations library.'''

AUTHOR="Luke Pinner"
AUTHOR_EMAIL="gdal.calculations@mailinator.com"
URL="https://github.com/lpinner/metageta"

CLASSIFIERS = [ 'Operating System :: OS Independent',
                'License :: OSI Approved :: MIT License',
                'Topic :: Scientific/Engineering :: GIS']

REQUIRED = ['GDAL >= 1.7, < 2.0','numpy >= 1.7']

if 'install' in sys.argv:
    for module in REQUIRED:
        try:__import__(module)
        except ImportError:raise ImportError('%s is required.'%module)

setupargs = {
    'name':'gdal_calculations',
    'version':version,
    'description':SHORTDESC,
    'long_description':LONGDESC,
    'platforms':['linux','windows','darwin'],
    'author':AUTHOR,
    'author_email':AUTHOR_EMAIL,
    'classifiers': CLASSIFIERS,
    'url':URL,
    'license':'MIT',
    'keywords':'raster calculations',
    'package_dir':{'': 'lib'},
    'packages':find_packages('lib'),
    'install_requires':REQUIRED,
    'package_data':{'gdal_calculations': ['README','COPYING','NEWS','VERSION']},
    'entry_points':{
        'console_scripts': [
            'gdal_calculate=gdal_calculations.gdal_calculate:main',
        ],
    }
}

setup(**setupargs)