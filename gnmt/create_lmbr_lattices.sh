#!/bin/bash
# Converts a lattice to an LMBR FST without a
# hypothesis space

if [ $# -ne 2 ] && [ $# -ne 3 ]; then
  echo "Usage: ./create_lmbr_lattices.sh <src_directory> <trgt_directory> [range]"
  echo "  Creates LMBR FSTs from lattices with an unrestricted hypotheses space."
  echo "    <src_directory>: source directory with FSTs "
  echo "    <trgt_directory>: directory to write the LMBR lattices"
  echo "    <range>: <from-idx>:<to-idx> (both inclusive). If not set, read all FSTs"
  exit 1;
fi

source $(dirname $0)/import_sgnmt_environment.sh
mkdir -p $2
range="$3"

if [ -z "$range" ]; then
  ids=$(ls $1/*.fst* | xargs -n 1 basename | cut -d'.' -f1 | sort -g)
else
  ids=$(seq $(echo $range | cut -d':' -f1) $(echo $range | cut -d':' -f2))
fi

which lmbr.O2

for id in $ids
do
  src_lat=$(ls $1/$id.fst*)
  #fstprint $src_lat | cut -f3 | sort -u -g | egrep -v '^[12]$' | awk 'BEGIN{print "0 1 1 1"}{print 1,1,$1,$1}END{print "1 2 2 2\n2"}' | fstcompile > tmp.hypo.fst
  #lmbr.O2 --load.evidencespace=$src_lat --load.hypothesesspace=tmp.hypo.fst --p 0.5278 --r 0.526 --writedecoder=tmp.decode.fst --logger.verbose
  lmbr.O2 --load.evidencespace=$src_lat --p 0.5278 --r 0.526 --logger.verbose &> tmp.log
  cat tmp.log  | fgrep 'printNgramPosteriors.INF:n-gram posterior' | sed 's/^.*printNgramPosteriors.INF:n-gram posterior //' > tmp.ngrams
  #fstpush --push_weights tmp.decode.fst $2/$(basename $src_lat)
done
