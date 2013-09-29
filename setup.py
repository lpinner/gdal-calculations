__version__='0.8dev'

import os,sys,warnings
from distutils.core import setup
sys.path.insert(0,'lib')


SHORTDESC='Simple tiled (or untiled if desired) raster calculations (AKA "map algebra")'

LONGDESC='''This package enables simple tiled (or untiled if desired) raster calculations
(AKA "map algebra") from the commandline or from within your python scripts.
There is a commandline raster calculator and a raster calculations library.'''

AUTHOR="Luke Pinner"
AUTHOR_EMAIL="gdal.calculations@maildrop.cc"
URL="https://code.google.com/p/gdal-calculations"

CLASSIFIERS = [ 'Operating System :: OS Independent',
                'License :: OSI Approved :: MIT License',
                'Topic :: Scientific/Engineering :: GIS',
                'Development Status :: 4 - Beta']

REQUIRED = ['osgeo.gdal','numpy']
RECOMMENDED=['numexpr']

script=os.path.join('bin', 'gdal_calculate')
scripts=[script,script+'.cmd']

setupkwargs={}

if 'sdist' not in sys.argv:
    if os.name=='nt':del scripts[0]
    else:del scripts[1]

if 'install' in sys.argv:
    for module in REQUIRED:
        try:__import__(module)
        except ImportError:warnings.warn('%s is required.')
    for module in RECOMMENDED:
        try:__import__(module)
        except ImportError:warnings.warn('%s is recommended.')
else:
    setupkwargs['data_files']=[
                ('',['README']),
                ('',['COPYING']),
                ('',['NEWS'])
               ]

if 'bdist' in sys.argv:
    from distutils.command.bdist_wininst import bdist_wininst as _bdist_wininst
    from distutils.command.bdist_wininst import __file__ as _bdist_file
    from sysconfig import get_python_version

    class bdist_wininst(_bdist_wininst):
        """Patched wininst to allow building from wininst-9.0*.exe. on linux
           and wininst-9.0-amd64.exe on Win32
        """
        def get_exe_bytes (self):
            cur_version = get_python_version()
            bv=9.0
            directory = os.path.dirname(_bdist_file)
            if self.plat_name != 'win32' and self.plat_name[:3] == 'win':
                sfix = self.plat_name[3:]
            else:
                sfix = ''

            filename = os.path.join(directory, "wininst-%.1f%s.exe" % (bv, sfix))
            f = open(filename, "rb")
            try:
                return f.read()
            finally:
                f.close()
    setupkwargs['cmdclass']={'bdist_wininst':bdist_wininst}

setup(
    name = 'gdal-calculations',
    version = __version__,
    license = 'MIT',
    description=SHORTDESC,
    long_description=LONGDESC,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    classifiers = CLASSIFIERS,
    url=URL,
    scripts=scripts,
    package_dir={'': 'lib'},
    packages=['gdal_calculations'],
    **setupkwargs
    )
