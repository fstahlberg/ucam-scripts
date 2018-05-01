#!/bin/bash
# This script uses the SRI nbest-lattice tool to combine hypothesis in a
# nbest list in Moses format.

if [ $# -ne 1 ]; then
  echo "Usage: ./combine_with_nbest_lattice.sh <moses-nbest-list> "
  echo "  Applies nbest-lattice to create a single combined hypothesis from an nbest list."
  echo "    <moses-nbest-list>: n-best list in moses format"
  exit 1;
fi

export LD_LIBRARY_PATH="/home/mifs/fs439/bin/gcc/gcc-4.9.3/lib64:$LD_LIBRARY_PATH"

TMP_NAME1=$(tempfile)
TMP_NAME2=$(tempfile)

nbest_file=$1

for id in $(cut -d' ' -f1 $nbest_file | uniq)
do
  egrep "^$id " $nbest_file > $TMP_NAME1
  echo "NBestList1.0" > $TMP_NAME2
  # Convert scores from log_e to log_10, then to bytelog
  cat $TMP_NAME1 | awk -F'|' '{print $10}' | awk '{print 0.4342944*$1}' | /home/mifs/fs439/bin/srilm/bin/i686-m64/log10-to-bytelog | paste -d'|' - $TMP_NAME1 | awk -F'|' '{print "("$1")"$5}' >> $TMP_NAME2
  /home/mifs/fs439/bin/srilm/bin/i686-m64/nbest-lattice -nbest $TMP_NAME2
done

rm $TMP_NAME1 $TMP_NAME2

