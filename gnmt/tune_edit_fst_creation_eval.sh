#!/bin/bash
# This script can be used as -evalCommand for MERT. See
# tune_edit_fst_creation.sh


# THIS IS BROKEN

if [ $# -ne 6 ]; then
  echo "Usage: ./tune_edit_fst_creation_eval.sh <hifst_directory> <nmt_directory> <work-dir> <range> <nmt-vocab> <coeff>"
  echo "  To be called from mert.jar as -evalCommand. See tune_edit_fst_creation.sh."
  echo "    <hifst_directory>: HiFST lattice directory (with same arc type as NMT directory)"
  echo "    <nmt_directory>: NMT lattice directory. OOVs should be marked with id $UNK_ID"
  echo "    <work_directory>: directory for temporary files"
  echo "    <range>: format: from-idx:to-idx (both inclusive)"
  echo "    <nmt-vocab>: nmt vocabulary size"
  echo "    <coeff>: Colon separated list of current coefficients: nmt-scale:edit-cost:ins-unk-cost:unk-to-in-vocab>"
  exit 1;
fi

hifst_dir=$1
nmt_dir=$2
work_dir=$3
range=$4
nmt_vocab=$5
coeff=$6
num_parts=40

echo "bash ../scripts/create_sparse_edit_fst_directory.sh $hifst_dir $nmt_dir $work_dir/lats \$GRID_ASSIGNED_RANGE $nmt_vocab "$(echo $coeff | tr ':' ' ')" 2000 3" > $work_dir/cmd.sh
mkdir -p $work_dir/log
rm -r $work_dir/lats

#bash ../scripts/grid/distribute_on_grid.sh $num_parts $range $work_dir/cmd.sh $work_dir/log
qsub -N distribute-on-grid-worker -l mem_free=50G,mem_grab=50G -o $work_dir/log -e $work_dir/log -t 1-$num_parts -v total_range=$range,num_parts=$num_parts,cmd_file=$work_dir/cmd.sh $(dirname $0)/grid/distribute_on_grid_worker.sh 

# Wait until finished..
n=$(echo "1-"$(echo $range | tr ':' '+') | bc)
i=0
while [ "$i" != "$n" ]
do
  echo $(date)": Waiting ($i/$n)..."
  sleep 30
  i=$(ls $work_dir/lats | wc -l)
done
sleep 10

