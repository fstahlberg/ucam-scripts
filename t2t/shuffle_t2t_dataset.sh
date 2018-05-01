#!/bin/bash

if [ $# -eq 0 ]; then
  echo "Usage: ../scripts/shuffle_t2t_dataset.sh <t2t-file-path-pattern>"
  exit 1;
fi

for filename in "$@"
do
  python $(dirname $0)/shuffle_t2t_dataset.py --input_filename $filename --output_filename tmp.shuffled
  cp tmp.shuffled $filename
done

rm tmp.shuffled
