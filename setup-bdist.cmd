python setup.py sdist --formats=gztar
python setup.py bdist_wheel
rmdir /S /Q build
pause