#!/bin/bash
# Create a nbest file in moses format 

if [ $# -ne 2 ]; then
  echo "Usage: ./create_moses_nbest_list.sh <n-best> <src_directory>"
  echo "  Creates a n-best list in Moses format from LATS created by ucam-smt."
  echo "    <n-best>: Depth of n-best list (n)"
  echo "    <src_directory>: ucam-smt lattice directory containing gzipped lattice files with (G+M,G) arcs"
  exit 1;
fi

source $(dirname $0)/import_hifst_environment.sh

id=1
while [ -f $2/$id.fst.gz ]
do
  printstrings.O2.bin --nbest=$1 --unique --weight --semiring=lexstdarc --input=$2/$id.fst.gz | sed 's/^\([ 0-9]\+\)\t\([-.0-9]\+\),.*$/'$(echo "$id-1" | bc)' ||| \1 ||| \2/'
  id=$(echo "1+$id" | bc)
done
