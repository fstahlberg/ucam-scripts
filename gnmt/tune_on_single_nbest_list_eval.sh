#!/bin/bash
# This script can be used as -evalCommand for MERT. See
# tune_edit_fst_creation.sh

if [ $# -ne 5 ]; then
  echo "Usage: ./tune_on_single_nbest_list.sh <dim> <moses-nbest-list> <work_directory> <bleu-cmd> <coeff>"
  echo "  Tunes rescoring an n-best list with BOBYQA."
  echo "    <dim>: Dimensionality"
  echo "    <nbest-list>: nbest list in Moses format with explicit feature breakdown. All features must be given for each nbest entry"
  echo "    <work_directory>: directory for temporary files"
  echo "    <bleu-cmd>: Command which reads indexed sentences from stdin and outputs a multi-bleu.pl style last line"
  exit 1;
fi

dim=$1
nbest=$2
work_dir=$3
bleu_cmd=$(echo $4 | tr '!' ' ')
coeff=$5

cat $nbest  | cut -d'|' -f7 | awk '{print "'$coeff'"$0}' | sed 's/:/ : /g' | awk '{acc = 0.0; for (i=2*'$dim'+1; i<=NF; i+=2){ acc += $(i-2*'$dim')*$i } print acc}' | paste -d' ' - $nbest | awk '{$NF = $1; print $0}' | sort -g -k1 -r| sort -k2 -g -s | cut -d' ' -f2- > $work_dir/nbest

cat $work_dir/nbest |  ../scripts/print_1best_in_nbest.sh > $work_dir/text

# Eval
source ~/.bashrc

eval_cmd="cat $work_dir/text | $bleu_cmd > $work_dir/bleu"
eval $eval_cmd
echo -$(tail -1 $work_dir/bleu | tr -d ',' | cut -d' ' -f3)
