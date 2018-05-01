#!/bin/bash
# This script reads out a directory created with GNMT
# containing VECLATS in text format and converts them
# to compiled FSTs with standard arcs

if [ $# -ne 3 ]; then
  echo "Usage: ./compile_veclat_directory_to_standard.sh <src_directory> <trgt_directory> <weights>"
  echo "  Reads a FST directory created with GNMT in text format, compiles the lattices, and stores them with standard arcs."
  echo "     src_directory: Directory with GNMT lattices in text format (veclats)."
  echo "     trgt_directory: Directory in which to write."
  echo "     weights: Comma separated weights without gamma (see GNMT's --predictor_weights)."
  exit 1;
fi

source $(dirname $0)/import_hifst_environment15.sh
mkdir -p $2

for src_lat in $(ls $1/*.fst.txt)
do
  trg_lat=$2/$(basename $src_lat .txt)
  cat $src_lat | python $(dirname $0)/fst_sparse2standard.py -w "$3" | fstcompile > $trg_lat
done
