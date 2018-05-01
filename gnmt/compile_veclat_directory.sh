#!/bin/bash
# This script reads out a directory created with GNMT
# containing VECLATS in text format and compiles, determinizes,
# and minimizes them

if [ $# -ne 2 ] && [ $# -ne 3 ] && [ $# -ne 4 ]; then
  echo "Usage: ./compile_veclat_directory.sh <src_directory> <trgt_directory> [params [previous_directory]]"
  echo "  Reads a FST directory created with GNMT in text format, compiles, determinizes, and minimizes"
  echo "  the lattices, and writes them into the target directory."
  echo "previous_directory: If given, load FSTs from that directory and union them."
  echo "params: Set environment variable PARAM to this value."
  exit 1;
fi

source $(dirname $0)/import_hifst_environment15.sh
mkdir -p $2

export TUPLEARC_WEIGHT_VECTOR="$3"
export PARAMS="$3"
TMP_NAME=$(tempfile)
for src_lat in $(ls $1/*.fst.txt)
do
  trg_lat=$2/$(basename $src_lat .txt)
  if [ -z "$4" ]; then
    fstcompile --arc_type=tropicalsparsetuple $src_lat | fstdeterminize | fstminimize > $trg_lat
  else
    zcat $4/$(basename $src_lat .txt).gz > $TMP_NAME
    fstcompile --arc_type=tropicalsparsetuple $src_lat | fstunion - $TMP_NAME | fstdeterminize | fstminimize > $trg_lat
  fi
  gzip $trg_lat
done
rm $TMP_NAME

unset TUPLEARC_WEIGHT_VECTOR
unset PARAMS
