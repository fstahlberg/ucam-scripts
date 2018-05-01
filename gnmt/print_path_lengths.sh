#!/bin/bash

if [ $# -ne 1 ]; then
  echo "Usage: ./print_path_lengths.sh <src_directory>"
  echo "  Prints distribution over path lengths in 1000 best lists."
  echo "    <src_directory>: ucam-smt lattice directory"
  exit 1;
fi

source $(dirname $0)/import_hifst_environment.sh

for src_lat in $(ls -v $1/*.fst)
do
  cat $src_lat | fstmap --map_type=to_standard | printstrings.O2 -n 1000 -w | awk '{print NF-3" "$NF}' | sort -g -k1 | awk '{if ($1 != last) {print ""; last=$1} print $0}' | tail -n +2 | sed 's/^$/X/' | tr "\n" ' ' | tr 'X' "\n" | sed 's/^ *//' | awk '{acc = 0.0; for (i=2;i<=NF;i+=2) {acc += exp(-$i)} print $1" "log(acc)}' | tr "\n" "X" | sed 's/X/ X /g' | awk '{acc = 0.0; for (i=2;i<=NF;i+=3) {acc += exp($i)}; acc=log(acc); for (i=2;i<=NF;i+=3) {$i-=acc} print $0}' | tr ' ' ':' | sed 's/:X:/ /g' | sed 's/[:X]\+$//'
done

