#!/bin/bash
# This script can be used as -evalCommand for MERT.

if [ $# -ne 6 ]; then
  echo "Usage: ./mert_single_best_eval.sh <config_file> <range> <num_parts> <work_directory> <bleu-cmd> <coeff>"
  echo "  Tunes single best SGNMT output with BOBYQA."
  echo "    <config_file>: SGNMT config file (must not include predictor_weights, range, or outputs"
  echo "    <range>: Range of sentence ids (e.g. 1:2737)"
  echo "    <num_parts>: Number of jobs in the SGD array"
  echo "    <work_directory>: directory for temporary files"
  echo "    <bleu-cmd>: Command which reads indexed sentences from stdin and outputs a multi-bleu.pl style last line"
  exit 1;
fi

config_file=$1
range=$2
num_parts=$3
work_dir=$4/sgnmt
bleu_cmd=$(echo $5 | tr '!' ' ')
coeff=$6

decode_script=$(dirname $0)/decode_on_grid_cpu.sh
#decode_script=$(dirname $0)/decode_on_grid_cpu_mediummem.sh

rm -r $work_dir
mkdir -p $work_dir

# Create config file
cp $config_file $work_dir/config.ini
echo "outputs: text,nbest" >>  $work_dir/config.ini

n_pred=$(cat $config_file  | egrep '^ *predictors *:' | cut -d':' -f2- | awk -F',' '{print NF}')
dim=$(echo $coeff | awk -F':' '{print NF}')
if [ "$n_pred" == "$dim" ]
then
  echo "predictor_weights: "$(echo $coeff | tr ':' ',') >>  $work_dir/config.ini
else
  echo "predictor_weights: "$(echo $coeff | awk -F':' '{s = $1/('$n_pred'-'$dim'+1.0); print s; for (i=2;i<='$n_pred';i++) {print("," (i<=NF ? $i : s))}}'  | tr -d "\n") >>  $work_dir/config.ini
fi

# Run decoder
cmd="$decode_script $num_parts $range $work_dir/config.ini $work_dir"
echo "DECODE CMD:$cmd"
eval $cmd

# Wait
while [ ! -f $work_dir/DONE ]
do
  echo $(date)": Waiting for $work_dir/DONE..."
  sleep 30
done

echo "Start evaluation..."
# Eval
source ~/.bashrc

eval_cmd="cat $work_dir/out.text | $bleu_cmd > $work_dir/bleu"
eval $eval_cmd
echo -$(tail -1 $work_dir/bleu | tr -d ',' | cut -d' ' -f3)
