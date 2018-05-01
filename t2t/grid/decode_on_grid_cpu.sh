#!/bin/bash

if [ $# -ne 4 ] && [ $# -ne 5 ]; then
  echo "Usage: ./decode_on_grid_cpu.sh <num-parts> <total-range> <sgnmt-config-file> <output-dir> [<mem_required>]"
  echo "  This script distributes T2T decoding on the <num-parts> CPU nodes on the GRID engine."
  echo "    <num-parts>: Number of jobs"
  echo "    <total-range>: Index range <from-idx>:<to-idx> (both inclusive)"
  echo "    <sgnmt-config-file>: Full SGNMT .ini file"
  echo "    <output-dir>: The outputs of each job will be written to <out-dir>/job-id/out.%s"
  echo "                  Combined files are created with the prefix <out-dir>/out.%s"
  echo "                  Logs are stored in <out-dir>/logs"
  echo "                  The output formats are specified via <sgnmt-config-file>"
  echo "    <mem_required>: Memory requirement (default: 1.5G)"
  exit 1;
fi

num_parts=$1
total_range=$2
config_file=$3
output_dir=$4
worker_script=$(dirname $0)/decode_on_grid_cpu_worker.sh
combination_script=$(dirname $0)/decode_on_grid_cpu_combination.sh
mem_required="$5"
if [ -z "$mem_required" ]; then
  mem_required="1.5G"
fi

mkdir -p $output_dir/logs

# Start workers
echo "Decode $total_range sentences using $config_file with $num_parts workers ($mem_required), writing to $output_dir..."
ID=$(qsub -N sgnmt-worker -l "mem_free=$mem_required,mem_grab=$mem_required,osrel=14.04" -o $output_dir/logs -e $output_dir/logs -t 1-$num_parts -v config_file=$config_file,num_parts=$num_parts,total_range=$total_range,output_dir=$output_dir $worker_script | awk '{print $3}' | sed 's:\..*::')
HT="-hold_jid $ID"

# Start combination job
qsub -N sgnmt-combination -l 'osrel=*' -o $output_dir/logs -e $output_dir/logs $HT -v output_dir=$output_dir,num_parts=$num_parts $combination_script

