#!/bin/bash
# This script uses Apache commons BOBYQA implementation
# to optimize the 1-best hypothesis on a single n-best list through rescoring

if [ $# -ne 4 ]; then
  echo "Usage: ./tune_on_single_nbest_list.sh <dim> <moses-nbest-list> <work_directory> <bleu-cmd>"
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
# We need to replace the spaces in bleu_cmd because otherwise mert.jar interprets it as separate arguments
bleu_cmd=$(echo $4 | tr ' ' '!')

mkdir -p $work_dir


#/home/mifs/fs439/bin/jdk1.8.0_65/bin/java -jar ~/bin/mert/mert.jar -minWeight 0.0001 -sumEq1 1 -algorithm bobyqa -dim $dim -outputPrefix $work_dir/mert -evalCommand "$(dirname $0)/tune_on_single_nbest_list_eval.sh $dim $nbest $work_dir $bleu_cmd"
/home/mifs/fs439/bin/jdk1.8.0_65/bin/java -jar ~/bin/mert/mert.jar -minWeight 0.0001 -algorithm simplex -dim $dim -outputPrefix $work_dir/mert -evalCommand "$(dirname $0)/tune_on_single_nbest_list_eval.sh $dim $nbest $work_dir $bleu_cmd"

