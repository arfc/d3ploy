rm cyclus.sqlite
rm log.txt
rm POWER.txt
rm -r build
python setup.py install
cyclus decom.xml
cat log.txt
cat POWER.txt