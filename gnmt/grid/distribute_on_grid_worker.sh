#!/bin/sh
#
# the next line is a "magic" comment that tells gridengine to use bash
#$ -S /bin/bash
#
# and now for some real work

# Following variables must be set:
# $SGE_TASK_ID task id (ranging from 1 to $num_parts (inclusive))
# $total_range total ID range of the task
# $num_parts number of jobs
# $cmd_file command file to source

vars="$SGE_TASK_ID:$total_range:"$(echo "$num_parts:$total_range" | awk -F':' '{val = (1+$3-$2)/$1; print (val == int(val)) ? val : int(val)+1}')
# vars stores task_id:from:to:part_size
start_idx=$(echo $vars | awk -F':' '{print $2+($1-1)*$4}')
end_idx=$(echo $vars | awk -F':' '{val = $2+$1*$4-1; print val < $3 ? val : $3}')

if [ "$start_idx" -gt "$end_idx" ]; then
  echo "Nothing to do for worker $SGE_TASK_ID"
  exit
fi
echo "Range for worker $SGE_TASK_ID: $start_idx:$end_idx"

export GRID_ASSIGNED_RANGE=$start_idx:$end_idx

source $cmd_file


