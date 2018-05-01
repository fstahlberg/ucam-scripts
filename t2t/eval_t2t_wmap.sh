#!/bin/bash

export LC_ALL=en_GB.utf8

if [ $# -ne 3 ] && [ $# -ne 4 ]; then
  echo "Usage: ./eval_wat.sh <input-file-idx> <wmap> <raw-ref> [tokenization]"
  echo "or: ./eval_wat.sh <input-file-text> <ref>"
  echo "  BLEU evaluation script."
  echo "    <input-file-idx>: MT output (indexed)"
  echo "    <wmap>: wmap file (format: word id)"
  echo "    <ref>: Reference file (raw, untokenized)"
  echo "    <tokenization>: Tokenization passed through to apply_wmap: id (default), eow, mixed"
  exit 1;
fi

tok="$4"
if [ -z "$tok" ]; then
  tok="id"
fi

cat $1 | python /data/mifs_scratch/fs439/exp/gnmt/scripts/apply_wmap.py -m $2 -d i2s -t $tok | sed 's/<unk>/UNK/gi' | /data/mifs_scratch/fs439/bin/moses/scripts/recaser/detruecase.perl | /data/mifs_scratch/fs439/bin/moses/scripts/tokenizer/detokenizer.perl > tmp.bleu.hyp.raw


$(dirname $0)/eval_t2t.sh tmp.bleu.hyp.raw $3

