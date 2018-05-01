#!/bin/bash

export LC_ALL=en_GB.utf8

if [ $# -ne 2 ] && [ $# -ne 3 ] && [ $# -ne 4 ]; then
  echo "Usage: ./eval_wat_raw.sh <input-file-idx> <wmap> <raw-ref> [tokenization]"
  echo "or: ./eval_wat.sh <input-file-text> <ref>"
  echo "  BLEU evaluation script."
  echo "    <input-file-idx>: MT output (indexed)"
  echo "    <wmap>: wmap file (format: word id)"
  echo "    <ref>: Reference file (raw)"
  echo "    <tokenization>: Tokenization passed through to apply_wmap: id (default), eow, mixed"
  exit 1;
fi

outFile=$(tempfile)
outRefFile=$(tempfile)

if [ $# -eq 2 ]; then
  cat $1 | perl /data/mifs_scratch/fs439/exp/gnmt/jaen-wat/scoring/detok.pl | perl /data/mifs_scratch/fs439/exp/gnmt/jaen-wat/scoring/script.segmentation.distribution/z2h-utf8.pl | /data/mifs_scratch/fs439/bin/moses/scripts/tokenizer/tokenizer.perl -l en  > $outFile
  refFile="$2"
else
  tok="$4"
  if [ -z "$tok" ]; then
    tok="id"
  fi
  cat $1 | sed 's/^ *1 \+//' | sed 's/ \+2 *$//'  | python /data/mifs_scratch/fs439/exp/gnmt/scripts/apply_wmap.py -m $2 -d i2s -t $tok | sed 's/<epsilon>/UNK/g' | sed 's/<unk>/UNK/g' | perl /data/mifs_scratch/fs439/exp/gnmt/jaen-wat/scoring/detok.pl | perl /data/mifs_scratch/fs439/exp/gnmt/jaen-wat/scoring/script.segmentation.distribution/z2h-utf8.pl | /data/mifs_scratch/fs439/bin/moses/scripts/tokenizer/tokenizer.perl -l en  > $outFile
  refFile="$3"
fi

cat $refFile | perl /data/mifs_scratch/fs439/exp/gnmt/jaen-wat/scoring/detok.pl | perl /data/mifs_scratch/fs439/exp/gnmt/jaen-wat/scoring/script.segmentation.distribution/z2h-utf8.pl | /data/mifs_scratch/fs439/bin/moses/scripts/tokenizer/tokenizer.perl -l en  > $outRefFile


cat $outFile | /data/mifs_scratch/fs439/bin/moses/scripts/generic/multi-bleu.perl $outRefFile
cat $outFile | /data/mifs_scratch/fs439/bin/moses/scripts/generic/multi-bleu.perl -lc $outRefFile

cp $outFile tmp.bleu.hyp
cp $outRefFile tmp.bleu.ref
rm $outFile $outRefFile
