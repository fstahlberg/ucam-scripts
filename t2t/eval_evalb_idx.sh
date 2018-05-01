#!/bin/bash

export LC_ALL=en_GB.utf8

if [ $# -ne 3 ]; then
  echo "Usage: ../scripts/eval_evalb_idx.sh <vocab-file> <format> <evalb-ref-file> < indexed-hypos"
  echo "  F1 evaluation script evalb for indexed input (parsing)."
  echo "    <vocab-file>: T2T vocab file"
  echo "    <format>: Format of indexed data (layerbylayer, layerbylayer_pop, flat_bothtagged, flat_starttagged, flat_endtagged)"
  echo "    <evalb-ref-file>: Reference file for EVALB"
  exit 1;
fi

cat /dev/stdin | python $(dirname $0)/format_for_evalb.py --vocab_filename=$1 --input_format=$2 --output_format=evalb > tmp.evalb
cat tmp.evalb | python $(dirname $0)/unify_tree_tokenization.py -r $3 > tmp.evalb2
/data/mifs_scratch/fs439/bin/evalb/evalb -p /data/mifs_scratch/fs439/bin/evalb/new.prm $3 tmp.evalb2

