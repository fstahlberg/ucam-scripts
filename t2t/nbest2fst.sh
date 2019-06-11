#!/bin/bash

export LC_ALL=en_GB.utf8

if [ $# -ne 2 ]; then
  echo "Usage: ../scripts/eval_t2t.sh <nbest-file> <fst-directory>"
  echo "Inverts weights and adds <s> (ID: 2) and </s> (ID: 1)"
  exit 1;
fi

nbest_file=$1
fst_dir=$2

mkdir -p $fst_dir

for sen_id in $(cut -d' ' -f1 $nbest_file  | sort -u -g)
do
  fst_id=$(echo "$sen_id+1" | bc)
  egrep "^$sen_id " $nbest_file | cut -d'|' -f4,10 | tr '|' ':' | sed 's/^ */2 /' | sed 's/ *:/ 1:/' | python /data/mifs_scratch/fs439/exp/gnmt/scripts/compile_strings.py -i | fstcompile | fstdeterminize | fstminimize | fstrmepsilon | fstpush --push_weights > $fst_dir/$fst_id.fst
done


