#!/bin/bash

export LC_ALL=en_GB.utf8

if [ $# -ne 3 ]; then
  echo "Usage: ./eval.sh <input-file-idx> <wmap> <ref-unprocessed>"
  echo "  BLEU evaluation script."
  echo "    <input-file-idx>: MT output (indexed)"
  echo "    <wmap>: wmap file (format: word id)"
  echo "    <ref-unprocessed>: Reference file (not indexed, without unk and UNK)"
  exit 1;
fi

mkdir out.tmp

cat $1 | python /data/mifs_scratch/fs439/exp/gnmt/scripts/apply_wmap.py -m $2 -d i2s | sed 's/^ *<s> *//' | sed 's/ *<\/s> *$//' > out.tmp/out.txt

/home/mifs/fs439/bin/zgen/ScoreBLEU.sh -t out.tmp/out.txt -r $3 -odir out.tmp

