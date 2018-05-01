#!/bin/bash
# Applies a command chain to each file in a directory

if [ $# -ne 3 ] && [ $# -ne 4 ]; then
  echo "Usage: ./apply_to_directory.sh <src_directory> <trgt_directory> <cmd-chain> [range]"
  echo "  Applies a command chain to each file in a directory."
  echo "    <src_directory>: source directory with files of the form <id>.* "
  echo "    <trgt_directory>: directory to write the converted files"
  echo "    <cmd-chain>: Chain of command line tools to apply to the files in src_directory"
  echo "    <range>: <from-idx>:<to-idx> (both inclusive). If not set, read all files"
  exit 1;
fi

mkdir -p $2
cmd="$3"
range="$4"

if [ -z "$range" ]; then
  ids=$(ls $1/* | xargs -n 1 basename | cut -d'.' -f1 | sort -g)
else
  ids=$(seq $(echo $range | cut -d':' -f1) $(echo $range | cut -d':' -f2))
fi

for id in $ids
do
  src=$(ls $1/$id.*)
  full_cmd="cat $src | $cmd > "$2/$(basename $src)
  eval "$full_cmd"
done