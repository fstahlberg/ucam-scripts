#!/bin/bash

export LC_ALL=en_GB.utf8

if [ $# -ne 5 ]; then
  echo "Usage: ./eval_minmax_length.sh <input-file-idx> <wmap> <ref> <min-len> <max-len>"
  echo "  BLEU evaluation script with minimum and maximum source sentence length (multi-bleu)."
  echo "    <input-file-idx>: MT output (indexed)"
  echo "    <wmap>: wmap file (format: word id)"
  echo "    <ref>: Reference file (not indexed, (true)cased)"
  echo "    <min-len>: Minimum source sentence length (inclusive)"
  echo "    <max-len>: Maximum source sentence length (exclusive)"
  exit 1;
fi

outFile="out"
idsFile="tmp.ids"
preFile="tmp.pre"
refFile="out.ref"

cat $1 > $preFile

cat $3 | awk '{if (NF >= '$4' && NF < '$5') print NR}' > $idsFile
cat $idsFile | xargs -n 1 -IBLA sed 'BLAq;d' $3 > $refFile

cat $idsFile | xargs -n 1 -IBLA sed 'BLAq;d' $preFile | python /data/mifs_scratch/fs439/exp/gnmt/scripts/apply_wmap.py -m $2 -d i2s | sed 's/^ *<s> *//' | sed 's/ *<\/s> *$//' > $outFile
cat $outFile | /data/mifs_scratch/fs439/bin/moses/scripts/generic/multi-bleu.perl $refFile
cat $outFile | /data/mifs_scratch/fs439/bin/moses/scripts/generic/multi-bleu.perl -lc $refFile

