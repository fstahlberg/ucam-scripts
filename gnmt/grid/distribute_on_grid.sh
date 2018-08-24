#!/bin/bash

if [ $# -ne 4 ]; then
  echo "Usage: ./distribute_on_grid.sh <num-parts> <range> <cmd-file> <log-dir>"
  echo "  This script allows to distribute an arbitrary command over the grid nodes if it can be configured with a RANGE."
  echo "    <num-parts>: Number of jobs"
  echo "    <range>: Total range from_id:to_id (both inclusive)"
  echo "    <cmd_file>: Path to a file containing the command to execute. This command can use the \$GRID_ASSIGNED_RANGE placeholder"
  echo "                The script will set GRID_ASSIGNED_RANGE and then include the cmd_file via 'source'"
  echo "                Better specify an absolute path.."
  echo "    <log-dir>: Where to store the log files"
  exit 1;
fi

num_parts=$1
range=$2
cmd_file=$3
log_dir=$4
worker_script=$(dirname $0)/distribute_on_grid_worker.sh

mkdir -p $log_dir

qsub -N distribute-on-grid-worker -l 'not_host=air124,osrel=12.04' -o $log_dir -e $log_dir -t 1-$num_parts -v total_range=$range,num_parts=$num_parts,cmd_file=$cmd_file $worker_script 

