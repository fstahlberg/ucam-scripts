#!/bin/bash

if [ $# -ne 2 ]; then
  echo "Usage: ./moses_nbest_with_printstrings.sh <range> <printstrings-cmd> [no-invert]"
  echo "  Create a Moses style nbest list with HiFST's printstrings."
  echo "    <range>: format: from-idx:to-idx (both inclusive)"
  echo "    <printstrings-cmd>: printstrings command with ? placeholder for the sentence id"
  exit 1;
fi

source $(dirname $0)/import_hifst_environment15.sh
range=$1
printstrings_cmd="$2"

for id in $(seq $(echo $range | cut -d':' -f1) $(echo $range | cut -d':' -f2))
do
  moses_id=$(echo "$id-1" | bc)
  cmd=$(echo $printstrings_cmd | sed "s/\\?/$id/g")
  eval "$cmd" | sed 's/^ *1  *//' | sed "s/ *2 *\t/\t/" | awk -F"\t" '{$2=-$2; print "'$moses_id' ||| "$1" ||| "$2}' 
done
