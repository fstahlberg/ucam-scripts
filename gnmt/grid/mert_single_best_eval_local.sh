#!/bin/bash
# This script can be used as -evalCommand for MERT.

export LC_ALL=en_GB.utf8
source /data/mifs_scratch/fs439/exp/gnmt/scripts/import_sgnmt_environment_gpu.sh

if [ $# -ne 5 ]; then
  echo "Usage: ./mert_single_best_eval.sh <config_file> <range> <work_directory> <bleu-cmd> <coeff>"
  echo "  Tunes single best SGNMT output with BOBYQA."
  echo "    <config_file>: SGNMT config file (must not include predictor_weights, range, or outputs"
  echo "    <range>: Range of sentence ids (e.g. 1:2737)"
  echo "    <work_directory>: directory for temporary files"
  echo "    <bleu-cmd>: Command which reads indexed sentences from stdin and outputs a multi-bleu.pl style last line"
  exit 1;
fi

config_file=$1
range=$2
work_dir=$3/sgnmt
bleu_cmd=$(echo $4 | tr '!' ' ')
coeff=$5

rm -r $work_dir
mkdir -p $work_dir

# Create config file
cp $config_file $work_dir/config.ini
echo "outputs: text,nbest" >>  $work_dir/config.ini
echo "output_path: $work_dir/out.%s" >>  $work_dir/config.ini

n_pred=$(cat $config_file  | egrep '^ *predictors *:' | cut -d':' -f2- | awk -F',' '{print NF}')
dim=$(echo $coeff | awk -F':' '{print NF}')
if [ "$n_pred" == "$dim" ]
then
  echo "predictor_weights: "$(echo $coeff | tr ':' ',') >>  $work_dir/config.ini
else
  echo "predictor_weights: "$(echo $coeff | awk -F':' '{s = $1/('$n_pred'-'$dim'+1.0); print s; for (i=2;i<='$n_pred';i++) {print("," (i<=NF ? $i : s))}}'  | tr -d "\n") >>  $work_dir/config.ini
fi

# Run decoder
python $SGNMT/decode.py --config_file $work_dir/config.ini  --range $range &> $work_dir/log

echo "Start evaluation..."
# Eval
source ~/.bashrc

eval_cmd="cat $work_dir/out.text | $bleu_cmd > $work_dir/bleu"
eval $eval_cmd
echo -$(tail -1 $work_dir/bleu | tr -d ',' | cut -d' ' -f3)
