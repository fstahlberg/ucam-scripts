#!/bin/bash

if [ $# -ne 3 ]; then
  echo "Usage: ./decode_local.sh <sgnmt-config-file> <output-dir>"
  echo "  This script is a drop-in replacement for fast_decode_on_grid.sh for local decoding."
  echo "    <sgnmt-config-file>: Full SGNMT .ini file"
  echo "    <output-dir>: The output files are created with the prefix <out-dir>/out.%s"
  echo "                  Logs are stored in <out-dir>/log"
  echo "                  The output formats are specified via <sgnmt-config-file>"
  exit 1;
fi

source /data/mifs_scratch/fs439/exp/t2t/scripts/import_t2t_environment19.sh

config_file=$1
output_dir=$2
src_test="$(cat $config_file | egrep '^ *src_test *:' | cut -d':' -f2- | sed 's/ *//g')"
n_sentences=$(cat $src_test | wc -l)

echo "Decode $n_sentences sentences using $config_file locally, writing to $output_dir..."

python $SGNMT/decode.py --config_file $config_file --range 1:$n_sentences --t2t_usr_dir $USR_DIR --output_path $output_dir/out.%s &> $output_dir/log
touch $output_dir/DONE


