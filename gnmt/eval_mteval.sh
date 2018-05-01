#!/bin/bash
export LC_ALL="en_GB.utf8"

if [ $# -ne 4 ] && [ $# -ne 5 ]; then
  echo "Usage: ./eval-mteval.sh <lang> <wmap> <source> <ref> [<tokenization>] < <indexed-plain-text-hypotheses>"
  echo "  MTEval BLEU evaluation script. Applies deindexing, detokenization, detruecasing, and then runs mteval.pl"
  echo "  Last output line has same format as multi-bleu.pl"
  echo "    <lang>: Target language (en,fr...)"
  echo "    <wmap>: Target language word map file"
  echo "    <source>: Original source SGM file"
  echo "    <ref>: Original reference SGM file"
  echo "    <tokenization>: Tokenization passed through to apply_wmap: id (default), eow, mixed"
  echo "    <indexed-plain-text-hypos>: Indexed hypotheses are read from stdin"
  exit 1;
fi

out="out"
lang=$1
wmap=$2
src=$3
ref=$4

tok="$5"
if [ -z "$tok" ]; then
  tok="id"
fi

# We replace various UNK tokens to make sure that they do not temper
# with the internal tokenization of mteval-v13a.pl
# This might not be necessary in all cases but we want to be on the save side
cat /dev/stdin | python /data/mifs_scratch/fs439/exp/gnmt/scripts/apply_wmap.py -m $wmap -d i2s -t $tok | sed 's/<epsilon>/UNK/ig' | sed 's/<UNK>/UNK/ig' | sed 's/_UNK/UNK/ig' | sed 's/_NOTINWMAP/NOTINWMAP/ig' | sed 's/^ *<s> *//' | sed 's/ *<\/s> *$//' | /data/mifs_scratch/fs439/bin/moses/scripts/recaser/detruecase.perl | /data/mifs_scratch/fs439/bin/moses/scripts/tokenizer/detokenizer.perl -l $lang | perl /data/mifs_scratch/fs439/exp/gnmt/scripts/normalize-punctuation.perl de | perl /home/mifs/ech57/tools/mosesdecoder/scripts/ems/support/wrap-xml.perl $lang $src > $out.sgm

/data/mifs_scratch/fs439/bin/moses/scripts/generic/mteval-v13a.pl -r $ref -s $src -t $out.sgm -d 3 > $out.eval

cat $out.eval | tr "\n" ' ' | sed 's/Cumulative.*$//' | sed 's/^.*length ratio: \([0-9.-]\+\) (\([0-9.-]\+\)\/\([0-9.-]\+\)), penalty (log): \([0-9.-]\+\).*BLEU score = \([0-9.-]\+\) .*BLEU:/\1 \2 \3 \4 \5/' | awk '{print "BLEU = "($5*100)", "($6*100)"/"($7*100)"/"($8*100)"/"($9*100)" (BP="exp($4)", ratio="$1", hyp_len="$2", ref_len="$3")"}'

