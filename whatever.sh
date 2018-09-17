rm -rf build
python setup.py install 
rm tests/cyclus.sqlite
cyclus tests/test_cycamore.xml