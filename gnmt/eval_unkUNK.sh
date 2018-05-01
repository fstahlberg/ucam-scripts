#!/bin/bash

export LC_ALL=en_GB.utf8

if [ $# -ne 4 ]; then
  echo "Usage: ./eval.sh <input-file-idx> <wmap> <ref-processed> <ref-unprocessed"
  echo "  BLEU evaluation script."
  echo "    <input-file-idx>: MT output (indexed)"
  echo "    <wmap>: wmap file (format: word id)"
  echo "    <ref-processed>: Reference file (not indexed, with unk and UNK)"
  echo "    <ref-unprocessed>: Reference file (not indexed, without unk and UNK)"
  exit 1;
fi

mkdir out.tmp

cat $1 | python /data/mifs_scratch/fs439/exp/gnmt/scripts/apply_wmap.py -m $2 -d i2s | sed 's/^ *<s> *//' | sed 's/ *<\/s> *$//' > out.tmp/out.txt

python $(dirname $0)/randomly_replace_unkUNK.py --generated_reordering_with_unk out.tmp/out.txt --gold_unprocessed $4 --gold_processed $3 --out_file out.tmp/out.txt.replaced --remove_npsyms

/home/mifs/fs439/bin/zgen/ScoreBLEU.sh -t out.tmp/out.txt.replaced -r $4 -odir out.tmp

