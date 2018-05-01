#!/bin/bash

export LC_ALL=en_GB.utf8

if [ $# -ne 2 ] && [ $# -ne 3 ]; then
  echo "Usage: ../scripts/eval_t2t.sh <raw-hyp-file> <raw-ref-file> [<lang>]"
  echo "  BLEU evaluation script from tensor2tensor."
  echo "    <raw-hyp-file>: Untokenized decoding file"
  echo "    <raw-ref-file>: Tokenized reference file"
  echo "    <lang>: Target language (default: de)"
  exit 1;
fi

mosesdecoder=/data/mifs_scratch/fs439/bin/moses
untok_hyp_file=$1
untok_ref_file=$2
tok_hyp_file=$(tempfile)
tok_ref_file=$(tempfile)
atat_hyp_file=$(tempfile)
atat_ref_file=$(tempfile)
lang="$3"
if [ -z "$lang" ]; then
  lang="de"
fi


# Tokenize.
perl $mosesdecoder/scripts/tokenizer/tokenizer.perl -l $lang < $untok_hyp_file > $tok_hyp_file
perl $mosesdecoder/scripts/tokenizer/tokenizer.perl -l $lang < $untok_ref_file > $tok_ref_file

# Put compounds in ATAT format (comparable to papers like GNMT, ConvS2S).
# See https://nlp.stanford.edu/projects/nmt/ :
# 'Also, for historical reasons, we split compound words, e.g.,
#    "rich-text format" --> rich ##AT##-##AT## text format."'
perl -ple 's{(\S)-(\S)}{$1 ##AT##-##AT## $2}g' < $tok_hyp_file > $atat_hyp_file
perl -ple 's{(\S)-(\S)}{$1 ##AT##-##AT## $2}g' < $tok_ref_file > $atat_ref_file

# Get BLEU.
perl $mosesdecoder/scripts/generic/multi-bleu.perl $atat_ref_file < $atat_hyp_file
perl $mosesdecoder/scripts/generic/multi-bleu.perl -lc $atat_ref_file < $atat_hyp_file

cp $atat_ref_file tmp.bleu.ref
cp $atat_hyp_file tmp.bleu.hyp

rm $tok_hyp_file
rm $tok_ref_file
rm $atat_hyp_file
rm $atat_ref_file
