#!/bin/bash

if [ $# -ne 2 ]; then
  echo "Usage: ./invert_weights_in_fst_directory.sh <src_directory> <trgt_directory>"
  echo "  Reads all fsts in src_dir, applies fstmap -map_type=invert, and stores them in trg_directory"
  exit 1;
fi

source $(dirname $0)/import_hifst_environment15.sh
mkdir -p $2

for src_lat in $(ls $1/*.fst.gz)
do
  trg_lat=$2/$(basename $src_lat .gz)
  zcat $src_lat | fstmap -map_type=invert > $trg_lat
  gzip $trg_lat
done
