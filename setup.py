import os,sys
from distutils.core import setup

script=os.path.join('bin', 'gdal_calculate')
scripts=[script,script+'.cmd']

if 'sdist' not in sys.argv:
    if os.name=='nt':del scripts[0]
    else:del scripts[1]

setup(
    name = 'gdal-calculations',
    version = '0.1',
    description='GDAL calculations',
    author='Luke Pinner',
    author_email='gdal.calculations@maildrop.cc',
    url='https://code.google.com/p/gdal-calculations',
    scripts=scripts,
    package_dir={'': 'lib'},
    packages=['gdal_calculations'],
    )