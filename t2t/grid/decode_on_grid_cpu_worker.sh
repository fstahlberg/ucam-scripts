#!/bin/sh
#
#$ -S /bin/bash

source /data/mifs_scratch/fs439/exp/t2t/scripts/import_t2t_environment_cpu.sh

# This script requires the following variables (passed through by qsub via -v)
# SGE_TASK_ID: workers id (starting from 1)
# config_file: sgnmt config file
# num_parts: Total number of workers
# total_range: Total range of this array (not for this specific job)
# output_dir: Output directory (will write to <out_dir>/SGE_TASK_ID

# Get the ranges for this worker
if [ ! -z $SGE_TASK_ID ]; then
  if [[ $total_range != *":"* ]]
  then
    total_range="1:$total_range"
  fi
  vars="$SGE_TASK_ID:$total_range:"$(echo "$num_parts:$total_range" | awk -F':' '{val = (1+$3-$2)/$1; print (val == int(val)) ? val : int(val)+1}')
  # vars stores task_id:from:to:part_size
  start_idx=$(echo $vars | awk -F':' '{print $2+($1-1)*$4}')
  end_idx=$(echo $vars | awk -F':' '{val = $2+$1*$4-1; print val < $3 ? val : $3}')
else
  echo "This script needs to be called inside an array grid job! Exiting..."
  exit
fi
if [ "$start_idx" -gt "$end_idx" ]; then
  echo "Nothing to do for worker $SGE_TASK_ID"
  exit
fi
echo "Range for worker $SGE_TASK_ID: $start_idx:$end_idx"

# Start decoding
mkdir -p $output_dir/$SGE_TASK_ID
python $SGNMT/decode.py --config_file $config_file --range $start_idx:$end_idx --t2t_usr_dir $USR_DIR  --single_cpu_thread true --output_path $output_dir/$SGE_TASK_ID/out.%s


