#!/bin/bash

if [ $# -ne 4 ]; then
  echo "Usage: ./decode_on_grid_cpu.sh <num-parts> <total-range> <gnmt-config-file> <output-dir>"
  echo "  This script distributes decoding on the <num-parts> CPU nodes on the GRID engine."
  echo "    <num-parts>: Number of jobs"
  echo "    <total-range>: Index range <from-idx>:<to-idx> (both inclusive)"
  echo "    <gnmt-config-file>: Full specification of the GNMT decoding in .ini format"
  echo "    <output-dir>: The outputs of each job will be written to <out-dir>/job-id/out.%s"
  echo "                  Combined files are created with the prefix <out-dir>/out.%s"
  echo "                  Logs are stored in <out-dir>/logs"
  echo "                  The output formats are specified via gnmt-config-file"
  exit 1;
fi

num_parts=$1
total_range=$2
config_file=$3
output_dir=$4
worker_script=$(dirname $0)/decode_on_grid_cpu_worker.sh
combination_script=$(dirname $0)/decode_on_grid_cpu_combination.sh

mkdir -p $output_dir/logs

# Start workers
# We need to exclude air124 because of some problem with ATLAS on this host
ID=$(qsub -N gnmt-worker -pe memory_hog 2 -l 'not_host=air124,mem_free=1.5G,mem_grab=1.5G,osrel=*' -o $output_dir/logs -e $output_dir/logs -t 1-$num_parts -v config_file=$config_file,num_parts=$num_parts,total_range=$total_range,output_dir=$output_dir $worker_script | awk '{print $3}' | sed 's:\..*::')
HT="-hold_jid $ID"

# Start combination job
qsub -N gnmt-combination -o $output_dir/logs -e $output_dir/logs $HT -v output_dir=$output_dir,num_parts=$num_parts $combination_script

