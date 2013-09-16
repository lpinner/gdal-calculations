#!/bin/bash
python setup.py sdist --formats=gztar
python setup.py bdist --format=wininst --plat-name=win-amd64
python setup.py bdist --format=wininst --plat-name=win32
rm -rf build

