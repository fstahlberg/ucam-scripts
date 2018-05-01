#!/bin/bash
# This script reads out RTNs created with hifst
# and creates another directory which can be read by the rtn
# predictor in gnmt. Following steps are applied:
# - lex2std mapping (G+M,G) -> (G)
# - relabel HiFST special symbols like OOV, GAP, DR to epsilon
# - remove epsilon transitions
# - determinize
# - minimize

if [ $# -ne 2 ] && [ $# -ne 3 ]; then
  echo "Usage: ./create_rtn_directory.sh <src_directory> <trgt_directory> [<id-offset>]"
  echo "  Creates a GNMT readable directory from RTNs created by ucam-smt."
  echo "    <src_directory>: ucam-smt rtn directory"
  echo "    <trgt_directory>: directory to write the converted fsts"
  echo "    <id-offset>: Works only for numeric file names. Adds an integer to the lattice id"
  exit 1;
fi

source $(dirname $0)/import_hifst_environment.sh
src_dir="$1"
trgt_dir="$2"
id_offset=$3

RELABEL_FILE=/data/mifs_scratch/fs439/exp/gnmt/common/hifst_special_symbol_to_eps_map
NUMERIC_PATTERN='^[0-9]+$'

if [ ! -f $src_dir/ntmap ]; then
  echo "Could not find ntmap in source directory!"
  exit 1
fi
mkdir -p $trgt_dir
cp $src_dir/ntmap $trgt_dir

for src_id in $(ls $src_dir)
do
  if ! [[ $src_id =~ $NUMERIC_PATTERN ]] ; then
    continue
  fi
  if [ -z "$id_offset" ]; then
    trgt_id=$src_id
  else
    trgt_id=$(echo "$id_offset+$src_id"| bc)
  fi
  mkdir $trgt_dir/$trgt_id
  for src_lat in $(ls $src_dir/$src_id/*.fst)
  do
    cat $src_lat | lexmap.O2.bin --action=lex2std | fstrelabel -relabel_ipairs=$RELABEL_FILE -relabel_opairs=$RELABEL_FILE | fstrmepsilon | fstdeterminize | fstminimize > $trgt_dir/$trgt_id/$(basename $src_lat)
  done
done
