#!/bin/bash
# This script requires two fst directories with compiled fsts. Lets call them
# NMT and HiFST dirs.
# This script does the following steps for each FST in the directories:
# 1.) Load the FST vocabulary from HiFST 
# 2.) Create a FST consisting of 1 state accepting all strings with words of this vocabulary
# 3.) Replace epsilon (UNK) arcs in the NMT FST with this acceptor
# 4.) Union the newly created FST with the HiFST FST
# printstrings on the resulting FSTs results in translations which have scores from both systems
# NMT UNKs can be fixed by the guidance of the added HiFST scores

if [ $# -ne 3 ]; then
  echo "Usage: ./create_fst_directory.sh <hifst_directory> <nmt_directory> <trgt_directory>"
  echo "  Creates a FST with scores from HiFST and NMT."
  echo "    <src_directory>: HiFST lattice directory (with same arc type as NMT directory)"
  echo "    <nmt_directory>: NMT lattice directory"
  echo "    <trgt_directory>: directory to write the converted lattices"
  exit 1;
fi

source $(dirname $0)/import_hifst_environment.sh
hifst_dir=$1
nmt_dir=$2
trgt_dir=$3
mkdir -p $trgt_dir

TMP_HIFST=$(tempfile)
TMP_NMT=$(tempfile)
TMP_VOCAB=$(tempfile)
TMP_UNK=$(tempfile)
TMP_RELABEL_FILE=$(tempfile)
TMP_REPLACED=$(tempfile)

UNK_ID=3333333
ROOT_ID=3333334

echo "0 $UNK_ID" > $TMP_RELABEL_FILE

for hifst_lat in $(ls $hifst_dir/*.fst*)
do
  id=$(basename $hifst_lat | cut -d'.' -f1)
  echo "id: $id"
  nmt_lat=$(ls $nmt_dir/$id.fst*)
  if [[ $hifst_lat == *.gz ]]; then
    zcat $hifst_lat | fstmap --map_type=to_standard > $TMP_HIFST
  else
    cat $hifst_lat | fstmap --map_type=to_standard > $TMP_HIFST
  fi
  if [[ $nmt_lat == *.gz ]]; then
    zcat $nmt_lat | fstrelabel --relabel_ipairs=$TMP_RELABEL_FILE --relabel_opairs=$TMP_RELABEL_FILE > $TMP_NMT
  else
    cat $nmt_lat | fstrelabel --relabel_ipairs=$TMP_RELABEL_FILE --relabel_opairs=$TMP_RELABEL_FILE > $TMP_NMT
  fi
  fstprint $TMP_HIFST | cut -f3 | sort -g -u > $TMP_VOCAB
  cat $TMP_VOCAB | awk '{print "0 1 "$1" "$1"\n1 1 "$1" "$1}END{print "1"}' | fstcompile > $TMP_UNK
  fstreplace --epsilon_on_replace $TMP_NMT $ROOT_ID $TMP_UNK $UNK_ID > $TMP_REPLACED
  fstunion $TMP_HIFST $TMP_REPLACED | gzip -c > $trgt_dir/$id.fst.gz
done

rm $TMP_HIFST
rm $TMP_NMT
rm $TMP_VOCAB
rm $TMP_UNK
rm $TMP_RELABEL_FILE
rm $TMP_REPLACED
