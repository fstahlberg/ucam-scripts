#!/bin/bash
# This script reads out a directory created with GNMT
# containing lattices with standard arcs in text format and compiles them

if [ $# -ne 2 ]; then
  echo "Usage: ./compile_fst_directory.sh <src_directory> <trgt_directory>"
  echo "  Reads a FST directory created with GNMT in text format (sfst), compiles the lattices, and writes them into the target directory."
  exit 1;
fi

source $(dirname $0)/import_hifst_environment15.sh
mkdir -p $2

for src_lat in $(ls $1/*.fst.txt)
do
  trg_lat=$2/$(basename $src_lat .txt)
  fstcompile $src_lat > $trg_lat
  gzip $trg_lat
done
