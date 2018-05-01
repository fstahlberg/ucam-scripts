#!/bin/bash
# Applies a command chain to each FST in a directory

if [ $# -ne 3 ] && [ $# -ne 4 ]; then
  echo "Usage: ./apply_to_fst_directory.sh <src_directory> <trgt_directory> <cmd-chain> [range]"
  echo "  Applies a command chain to each FST in a directory."
  echo "    <src_directory>: source directory with FSTs "
  echo "    <trgt_directory>: directory to write the converted lattice"
  echo "    <cmd-chain>: Chain of FST tools to apply to the FSTs in src_directory"
  echo "    <range>: <from-idx>:<to-idx> (both inclusive). If not set, read all FSTs"
  exit 1;
fi

source $(dirname $0)/import_hifst_environment15.sh
mkdir -p $2
cmd="$3"
range="$4"

if [ -z "$range" ]; then
  ids=$(ls $1/*.fst* | xargs -n 1 basename | cut -d'.' -f1 | sort -g)
else
  ids=$(seq $(echo $range | cut -d':' -f1) $(echo $range | cut -d':' -f2))
fi

for id in $ids
do
  src_lat=$(ls $1/$id.fst*)
  if [[ $src_lat == *.gz ]]; then
    begin="zcat $src_lat"
    end=" | gzip -c"
  else
    begin="cat $src_lat"
    end=""
  fi
  full_cmd="$begin | $cmd $end > "$2/$(basename $src_lat)
  eval "$full_cmd"
done
