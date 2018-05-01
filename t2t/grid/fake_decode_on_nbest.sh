#!/bin/bash

if [ $# -lt 5 ] ; then
  echo "Usage: ./fake_decode_on_nbest.sh <nbest-list> <length_norm> <ignored> <sgnmt-config-file> <output-dir> [<ignored> ...]"
  echo "  Can be used in place of decode_on_grid_cpu.sh, but just reweights an nbest list."
  echo "    <nbest-list>: Path to the n-best list"
  echo "    <length_norm>: If set to 'length_norm', use length normalization"
  echo "    <sgnmt-config-file>: Full SGNMT .ini file"
  echo "    <output-dir>: The outputs of each job will be written to <out-dir>/job-id/out.%s"
  echo "                  Combined files are created with the prefix <out-dir>/out.%s"
  echo "                  Logs are stored in <out-dir>/logs"
  echo "                  The output formats are specified via <sgnmt-config-file>"
  exit 1;
fi

nbest_path=$1
config_file=$4
output_dir=$5
pred_weights=$(fgrep predictor_weights $config_file | cut -d' ' -f2-)

if [ "$2" = "length_norm" ]
then
  echo "Using length normalization..."
  cat $nbest_path | python /data/mifs_scratch/fs439/exp/gnmt/scripts/reweight_nbest.py -w $pred_weights > tmp.nbest
  /data/mifs_scratch/fs439/exp/gnmt/scripts/length_norm_nbest.sh tmp.nbest | /data/mifs_scratch/fs439/exp/gnmt/scripts/print_1best_in_nbest.sh > $output_dir/out.text
  rm tmp.nbest
else
  cat $nbest_path | python /data/mifs_scratch/fs439/exp/gnmt/scripts/reweight_nbest.py -w $pred_weights | /data/mifs_scratch/fs439/exp/gnmt/scripts/print_1best_in_nbest.sh > $output_dir/out.text
fi
touch $output_dir/DONE
