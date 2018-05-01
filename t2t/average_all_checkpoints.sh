#!/bin/bash

export LC_ALL=en_GB.utf8

if [ $# -ne 1 ]; then
  echo "Usage: ./average_all_checkpoints.sh <checkpoint-directory>"
  echo "  Averages all checkpoints in a directory and stores the average in the average/ subdir."
  echo "    <checkpoint-directory>: Directory with checkpoint files"
  exit 1;
fi

checkpoint_dir=$(echo $1 | sed 's,/*$,,')

eval_cmd="python /home/mifs/fs439/bin/tensor2tensor/tensor2tensor/utils/avg_checkpoints.py --output_path $checkpoint_dir/average/avg_"$(ls $checkpoint_dir/*.index | wc -l)" --prefix $checkpoint_dir/ --checkpoints "$(ls $checkpoint_dir/*.index | xargs -IBLA -n 1 basename BLA '.index' | awk '{printf ","$0}' | cut -d',' -f2-)
echo "Command: $eval_cmd"
eval $eval_cmd


