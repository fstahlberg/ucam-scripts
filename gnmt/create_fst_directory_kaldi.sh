#!/bin/bash
# This script reads out a LATS directory created with hifst
# and creates another directory which can be read by the fst
# predictor in gnmt. Following steps are applied:
# - unzip
# - lex2std mapping (G+M,G) -> (G)
# - relabel HiFST special symbols like OOV, GAP, DR to epsilon
# - remove epsilon transitions
# - determinize
# - minimize
# - push weights to initial state (make it stochastic)

if [ $# -ne 2 ] && [ $# -ne 3 ]; then
  echo "Usage: ./create_fst_directory_kaldi.sh <src_directory> <trgt_directory> [<id-offset>]"
  echo "  Creates a GNMT readable directory from LATS created by ucam-smt using determinizestar from Kaldi."
  echo "    <src_directory>: ucam-smt lattice directory containing gzipped lattice files with (G+M,G) arcs"
  echo "    <trgt_directory>: directory to write the converted lattice in (unzipped, standard arcs)"
  echo "    <id-offset>: Works only for numeric file names. Adds an integer to the lattice id"
  exit 1;
fi

source $(dirname $0)/import_hifst_environment.sh
export PATH="/data/mifs_scratch/fs439/bin/kaldi/src/fstbin/:$PATH"

mkdir -p $2
id_offset=$3

RELABEL_FILE=/data/mifs_scratch/fs439/exp/gnmt/common/hifst_special_symbol_to_eps_map

for src_lat in $(ls $1/*.fst.gz)
do
  if [ -z "$id_offset" ]; then
    trgt_lat=$(basename $src_lat .gz)
  else
    trgt_lat=$(echo "$id_offset+"$(basename $src_lat .fst.gz) | bc).fst
  fi
  if [ -f $2/$trgt_lat ];
  then
    echo "Skip $trgt_lat"
    continue
  fi
  zcat $src_lat | lexmap.O2.bin --action=lex2std | fstrelabel -relabel_ipairs=$RELABEL_FILE -relabel_opairs=$RELABEL_FILE | fstdeterminizestar | fstminimize | fstmap -map_type=to_log | fstpush --push_weights > $2/$trgt_lat 
done
