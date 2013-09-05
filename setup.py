import os,sys
from distutils.core import setup

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

setup(
    name = 'gdal-calculations',
    version = '0.2dev',
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
    )