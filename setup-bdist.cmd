python setup.py sdist  --formats=gztar
python setup.py bdist --format=wininst
"C:\Python27\ArcGISx6410.1\python.exe" setup.py bdist --format=wininst
rmdir /S /Q build
pause