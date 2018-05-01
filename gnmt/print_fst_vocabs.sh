#!/bin/bash

if [ $# -ne 1 ]; then
  echo "Usage: ./print_fst_vocabs.sh <src_directory>"
  echo "  Reads out lattice vocabularies."
  echo "    <src_directory>: ucam-smt lattice directory"
  exit 1;
fi

source $(dirname $0)/import_hifst_environment.sh

for src_lat in $(ls -v $1/*.fst)
do
  fstprint $src_lat | cut -f3 | sort -g -u | egrep -v '^1$' | tr "\n" ' '
  echo
done

