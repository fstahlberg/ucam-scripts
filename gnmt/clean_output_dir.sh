
rm -r $(find . -maxdepth 2 | egrep '\./[^/]+/[0-9]+$')
rm -r $(find . -maxdepth 2 | egrep '\./[^/]+/logs$')
