#!/bin/bash
# Creates a list of ngram posteriors from a lattice using 
# hifsts LMBR tool

if [ $# -ne 2 ] && [ $# -ne 3 ] && [ $# -ne 4 ]; then
  echo "Usage: ./create_ngram_posteriors.sh <src_directory> <trgt_directory> [range [maxorder]]"
  echo "  Creates ngram posterior lists using HiFSTs LMBR tool."
  echo "    <src_directory>: source directory with FSTs "
  echo "    <trgt_directory>: directory to write the ngram posterior lists"
  echo "    <range>: <from-idx>:<to-idx> (both inclusive). If not set, read all FSTs"
  echo "    <maxorder>: maximum n-gram order (default: 4)"
  exit 1;
fi

source $(dirname $0)/import_sgnmt_environment.sh
mkdir -p $2
range="$3"
maxorder="$4"

if [ -z "$maxorder" ]; then
  maxorder=4
fi

if [ -z "$range" ]; then
  ids=$(ls $1/*.fst* | xargs -n 1 basename | cut -d'.' -f1 | sort -g)
else
  ids=$(seq $(echo $range | cut -d':' -f1) $(echo $range | cut -d':' -f2))
fi

which lmbr.O2

for id in $ids
do
  src_lat=$(ls $1/$id.fst*)
  lmbr.O2 --load.evidencespace=$src_lat --p 0 --r 0 --maxorder $maxorder --logger.verbose 2>&1 | fgrep 'printNgramPosteriors.INF:n-gram posterior' | sed 's/^.*printNgramPosteriors.INF:n-gram posterior //' | egrep -v ': 0\.0+$' > $2/$(basename $src_lat .fst).txt
done
