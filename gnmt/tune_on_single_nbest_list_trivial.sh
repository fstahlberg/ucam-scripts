#!/bin/bash
# This script uses simple grid search to tune a single parameter. It is designed
# for tuning the weights between n-best list score and a rescorer model

if [ $# -ne 7 ]; then
  echo "Usage: ./tune_on_single_nbest_list_trivial.sh <moses-nbest-list> <work_directory> <start_min> <start_max> <num_eval> <iter> <bleu-cmd>"
  echo "  Tunes rescoring an n-best list (single parameter only)."
  echo "    <nbest-list>: nbest list in Moses format with explicit feature breakdown. All features must be given for each nbest entry"
  echo "    <work_directory>: directory for temporary files"
  echo "    <sum>: max value"
  echo "    <num_eval>: number of evaluations per iteration"
  echo "    <iter>: number of iterations"
  echo "    <bleu-cmd>: Command which reads indexed sentences from stdin and outputs a multi-bleu.pl style last line"
  exit 1;
fi

nbest=$1
work_dir=$2
min=$3
max=$4
num_eval=$5
n_iter=$6
# We need to replace the spaces in bleu_cmd because otherwise mert.jar interprets it as separate arguments
bleu_cmd=$(echo $7 | tr ' ' '!')
eval_cmd="bash $(dirname $0)/tune_on_single_nbest_list_eval.sh 2 $nbest $work_dir '$bleu_cmd'"

mkdir -p $work_dir

# Iteratively refine min and max and store scores in scores.csv
rm $work_dir/scores.csv
for iter in $(seq $n_iter)
do
  # Collect $num_eval new scores between $min and $max
  echo "start iteration $iter ($min:$max)"
  for val in $(seq $min $(echo "scale=8;($max-$min)/$num_eval" | bc) $max)
  do
    cmd="$eval_cmd $val:1 > $work_dir/eval.out" 
    echo "EXECUTE: $cmd"
    eval $cmd
    echo "$val "$(tail -1 $work_dir/eval.out) >> $work_dir/scores.csv
  done
  # Set new $min and $max by getting the range of the 3 best entries in scores.csv
done



#/home/mifs/fs439/bin/jdk1.8.0_65/bin/java -jar ~/bin/mert/mert.jar -minWeight 0.0001 -sumEq1 0 -bobyqaHighBound $max -algorithm simplex -dim $dim -outputPrefix $work_dir/mert -evalCommand "$(dirname $0)/tune_on_single_nbest_list_eval.sh $dim $nbest $work_dir $bleu_cmd"

