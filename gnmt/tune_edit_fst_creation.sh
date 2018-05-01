#!/bin/bash
# This script uses Apache commons BOBYQA implementation
# to tune the parameters for create_edit_fst_directory.sh

if [ $# -ne 6 ]; then
  echo "Usage: ./tune_edit_fst_creation.sh <hifst_directory> <nmt_directory> <work_directory> <range> <nmt-vocab> <bleu-cmd>"
  echo "  Tunes the parameter of create_edit_fst_directory.sh (nmt-scale, edit-cost, ins-unk-cost, unk-to-in-vocab) with BOBYQA."
  echo "    <hifst_directory>: HiFST lattice directory (with same arc type as NMT directory)"
  echo "    <nmt_directory>: NMT lattice directory. OOVs should be marked with id $UNK_ID"
  echo "    <work_directory>: directory for temporary files"
  echo "    <range>: format: from-idx:to-idx (both inclusive)"
  echo "    <nmt-vocab>: nmt vocabulary size"
  echo "    <bleu-cmd>: Command which reads indexed sentences from stdin and outputs a multi-bleu.pl style last line"
  exit 1;
fi

hifst_dir=$1
nmt_dir=$2
work_dir=$3
range=$4
nmt_vocab=$5
# We need to replace the spaces in bleu_cmd because otherwise mert.jar interprets it as separate arguments
bleu_cmd=$(echo $6 | tr ' ' '!')

mkdir -p $3


/home/mifs/fs439/bin/jdk1.8.0_65/bin/java -jar ~/bin/mert/mert.jar -minWeight 0.0001 -abs 0.0001 -rel 0.0000001 -sumEq1 0 -algorithm simplex -dim 4 -initializer 1.1884765625:7.736328125:6.5615234375:6.8046875 -outputPrefix $work_dir/mert -evalCommand "$(dirname $0)/tune_edit_fst_creation_eval.sh $hifst_dir $nmt_dir $work_dir $range $nmt_vocab $bleu_cmd"

