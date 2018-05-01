#!/bin/bash

if [ $# -ne 1 ] && [ $# -ne 2 ]; then
  echo "Usage: ./lookup_hypo_in_nbest.sh <lats_directory> [<nbest>]"
  echo "  Looks up the position of the hypotheses at stdin in a nbest list."
  echo "    <lats_directory>: LATS directory with lattices to generate nbest lists from"
  echo "    <nbest>: Depth of nbest lists (default: 20000)"
  exit 1;
fi

source $(dirname $0)/import_hifst_environment15.sh
lat_dir=$1
nbest=$2
if [ -z "$nbest" ]; then
  nbest=20000
fi

i=1
while read sen
do
  pos=$(printstrings.O2.bin --input=$lat_dir/$i.fst.gz -n $nbest -u | egrep -n "^$sen *$" | cut -d':' -f1)
  if [ -z "$pos" ]; then
    echo $nbest
  else
    echo $pos
  fi
  i=$(echo "$i+1" | bc)
done < /dev/stdin

