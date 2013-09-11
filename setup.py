__version__='0.5dev'

import os,sys
from distutils.core import setup
sys.path.insert(0,'lib')


SHORTDESC='Simple tiled (or untiled if desired) raster calculations (AKA "map algebra")'

LONGDESC='''
This package enables simple tiled (or untiled if desired) raster calculations
(AKA "map algebra") from the commandline or from within your python scripts.
There is a commandline raster calculator and a raster calculations library.'''

AUTHOR="Luke Pinner"
AUTHOR_EMAIL="gdal.calculations@maildrop.cc"
URL="https://code.google.com/p/gdal-calculations"

CLASSIFIERS = [ 'Operating System :: OS Independent',
                'License :: OSI Approved ::  MIT License',
                'Topic :: Scientific/Engineering :: GIS',
                'Development Status :: 4 - Beta']

REQUIRES = ['GDAL','numpy']
RECOMMENDS=['numexpr']

script=os.path.join('bin', 'gdal_calculate')
scripts=[script,script+'.cmd']

if 'sdist' not in sys.argv:
    if os.name=='nt':del scripts[0]
    else:del scripts[1]

if 'install' in sys.argv:
    try:
        from osgeo import gdal
        import numpy
    except ImportError:
        import warnings
        warnings.warn('osgeo (gdal) and numpy required')

setup(
    name = 'gdal-calculations',
    version = __version__,
	license = 'GPL',
	description=SHORTDESC,
	long_description=LONGDESC,
	author=AUTHOR,
	author_email=AUTHOR_EMAIL,
	classifiers = CLASSIFIERS,
	url=URL,
    install_requires=REQUIRES,
    extras_require=RECOMMENDS,
    scripts=scripts,
    package_dir={'': 'lib'},
    packages=['gdal_calculations'],
    data_files=[('',['README']),
                ('',['COPYING']),
                ('',['NEWS'])
               ],
    )
