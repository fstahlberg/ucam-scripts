#!/bin/bash
# This script requires two fst directories with compiled fsts. Lets call them
# NMT and HiFST dirs.
# This script does the following steps for each FST in the directories:
# 1.) Load the FST vocabulary from HiFST 
# 2.) Create an edit distance FST with the HiFST lattice vocabulary which allows free sub,ins,del of UNK
# 3.) Compose NMT HiFST with edit distance FST, and then with HiFST

UNK_ID=999999998
REPLACE_ID=999999988
ROOT_ID=999999888
#MAX_HIFST_STATES=1000000
MAX_HIFST_STATES=100000

if [ $# -ne 6 ] && [ $# -ne 7 ] && [ $# -ne 8 ]; then
  echo "Usage: ./create_sparse_edit_fst_directory.sh <hifst_directory> <nmt_directory> <trgt_directory> <range> <nmt-vocab> <nmt-scale>,<edit-cost>,<ins-unk-cost>,<unk-to-in-vocab>,<hifst-scale> [out-n-best [max-unk-mult]]"
  echo "  Creates a sparsetuple FST with scores from HiFST and NMT."
  echo "    <hifst_directory>: HiFST lattice directory (with same arc type as NMT directory)"
  echo "    <nmt_directory>: NMT lattice directory. OOVs should be marked with id $UNK_ID"
  echo "    <trgt_directory>: directory to write the converted lattices"
  echo "    <range>: format: from-idx:to-idx (both inclusive)"
  echo "    <nmt-vocab>: nmt vocabulary size"
  echo "    <nmt-scale>: cost for an editing operation (sub,del,ins)"
  echo "    <edit-cost>: cost for an editing operation (sub,del,ins)"
  echo "    <ins-unk-cost>: cost for each additional token produced by UNK"
  echo "    <unk-to-in-vocab-cost>: cost for substituing an UNK token with a word within the NMT vocabulary"
  echo "    <out-n-best>: Write only n best paths (if not given, write the complete combined FST)"
  echo "    <max-unk-mult>: Maximum number of UNK multiplications. Unlimited if not set"
  exit 1;
fi

source $(dirname $0)/import_hifst_environment15.sh
hifst_dir=$1
nmt_dir=$2
trgt_dir=$3
range=$4
nmt_vocab=$5
tuple_weights=$6
out_n_best=$7
max_unk_mult=$8
mkdir -p $trgt_dir

#TMP_UNK=tmp.unk
#TMP_UNK_TXT=tmp.unk.txt
#TMP_REPLACE=tmp.replace
#TMP_HIFST=tmp.hifst
#TMP_NMT=tmp.nmt
#TMP_NMT_PRE=tmp.nmt.pre
#TMP_VOCAB_HIFST=tmp.vocab.hifst
#TMP_VOCAB_NMT=tmp.vocab.nmt
#TMP_EDIT=tmp.edit
#TMP_EDIT_TXT=tmp.edit.txt
#TMP_COMPOSED=tmp.composed

TMP_UNK=$(tempfile)
TMP_UNK_TXT=$(tempfile)
TMP_REPLACE=$(tempfile)
TMP_HIFST=$(tempfile)
TMP_NMT_PRE=$(tempfile)
TMP_NMT=$(tempfile)
TMP_VOCAB_HIFST=$(tempfile)
TMP_VOCAB_NMT=$(tempfile)
TMP_EDIT=$(tempfile)
TMP_EDIT_TXT=$(tempfile)
TMP_COMPOSED=$(tempfile)

export TUPLEARC_WEIGHT_VECTOR="$tuple_weights"

# Create UNK replacement FST
rm $TMP_UNK_TXT
if [ -z "$max_unk_mult" ]; then
  # Unlimited number of unk multiplications
  echo "0 1 $UNK_ID $UNK_ID" >> $TMP_UNK_TXT
  echo "1 1 $UNK_ID $UNK_ID 0,3,1.0" >> $TMP_UNK_TXT
  echo "1" >> $TMP_UNK_TXT
else
  # Limited number of unk multiplications: left-to-right topology with skip connections to final state
  prev_state=0
  for state in $(seq 1 $(echo "$max_unk_mult-1" | bc))
  do
    echo "$prev_state $state $UNK_ID $UNK_ID 0,3,1.0" >> $TMP_UNK_TXT
    echo "$prev_state $max_unk_mult $UNK_ID $UNK_ID" >> $TMP_UNK_TXT
    prev_state=$state
  done
  echo "$prev_state $max_unk_mult $UNK_ID $UNK_ID" >> $TMP_UNK_TXT
  echo "$max_unk_mult" >> $TMP_UNK_TXT
  # Allow unk deletion
  echo "0 $max_unk_mult $UNK_ID 0 0,4,1.0" >> $TMP_UNK_TXT
fi
fstcompile --arc_type=tropicalsparsetuple $TMP_UNK_TXT | fstarcsort --sort_type=olabel > $TMP_UNK

# Create relabel file which replaces the UNKs in the NMT lattice with the replace label
echo "$UNK_ID $REPLACE_ID" > $TMP_REPLACE

# Iterate through range
for id in $(seq $(echo $range | cut -d':' -f1) $(echo $range | cut -d':' -f2))
do
  echo "id: $id"
  
  # Load FSTs and vocabulary
  nmt_lat=$(ls $nmt_dir/$id.fst*)
  hifst_lat=$(ls $hifst_dir/$id.fst*)
  if [[ $hifst_lat == *.gz ]]; then
    #zcat $hifst_lat | fstmap --map_type=to_standard | fstprune --nstate=$MAX_HIFST_STATES | fstrmepsilon | fstdeterminize | fstminimize | vecmap.O2.bin --tuplearc --k=4 | fstarcsort --sort_type=olabel > $TMP_HIFST
    zcat $hifst_lat | fstmap --map_type=to_standard | fstprune --nstate=$MAX_HIFST_STATES | fstrmepsilon | vecmap.O2.bin --tuplearc --k=4 | fstarcsort --sort_type=olabel > $TMP_HIFST
  else
    cat $hifst_lat | fstmap --map_type=to_standard | fstprune --nstate=$MAX_HIFST_STATES | fstrmepsilon | vecmap.O2.bin --tuplearc --k=4 | fstarcsort --sort_type=olabel > $TMP_HIFST
  fi
  if [[ $nmt_lat == *.gz ]]; then
    zcat $nmt_lat | fstrelabel --relabel_ipairs=$TMP_REPLACE --relabel_opairs=$TMP_REPLACE | fstrmepsilon | fstdeterminize | fstminimize | vecmap.O2.bin --tuplearc --k=0 > $TMP_NMT_PRE
  else
    cat $nmt_lat | fstrelabel --relabel_ipairs=$TMP_REPLACE --relabel_opairs=$TMP_REPLACE | fstrmepsilon | fstdeterminize | fstminimize | vecmap.O2.bin --tuplearc --k=0 > $TMP_NMT_PRE
  fi
  # Following operations on the NMT lattice
  # 1.) Replace UNK ids with REPLACE ID
  # 2.) Replace REPLACE ID with the UNK FST which accepts a single UNK token and additional UNK tokens at cost unk_cost
  # 3.) remove epsilon, determinize, minimize
  # 4.) scale the weights
  # 5.) arc sort to make fstcompose work
  fstreplace --epsilon_on_replace $TMP_NMT_PRE $ROOT_ID $TMP_UNK $REPLACE_ID | fstrmepsilon | fstarcsort --sort_type=olabel > $TMP_NMT
  fstprint $TMP_HIFST | cut -f3 | sort -g -u > $TMP_VOCAB_HIFST
  fstprint $TMP_NMT | cut -f3 | sort -g -u | egrep -v "^$UNK_ID$" > $TMP_VOCAB_NMT

  # Create edit distance transducer
  rm $TMP_EDIT_TXT
  #echo "0 0 $UNK_ID 0 0,2,1.0" >> $TMP_EDIT_TXT
  for nmt_word in $(cat $TMP_VOCAB_NMT)
  do # Deletions
    echo "0 0 $nmt_word 0 0,2,1.0" >> $TMP_EDIT_TXT 
  done
  for hifst_word in $(cat $TMP_VOCAB_HIFST)
  do # unk substitution (for free) and insertions
    echo "0 0 0 $hifst_word 0,2,1.0" >> $TMP_EDIT_TXT
    if [[ "$hifst_word" -gt "$nmt_vocab" ]];
    then
      echo "0 0 $UNK_ID $hifst_word" >> $TMP_EDIT_TXT
    else
      echo "0 0 $UNK_ID $hifst_word 0,4,1.0" >> $TMP_EDIT_TXT
    fi
  done
  for nmt_word in $(cat $TMP_VOCAB_NMT)
  do # substitutions
    for hifst_word in $(cat $TMP_VOCAB_HIFST)
    do
      if [[ $nmt_word == $hifst_word ]]
      then
        echo "0 0 $nmt_word $hifst_word" >> $TMP_EDIT_TXT
      else
        echo "0 0 $nmt_word $hifst_word 0,2,1.0" >> $TMP_EDIT_TXT
      fi
    done
  done
  echo "0" >> $TMP_EDIT_TXT
  fstcompile --arc_type=tropicalsparsetuple $TMP_EDIT_TXT | fstarcsort --sort_type=olabel > $TMP_EDIT

  # Compose to final FST
  fstcompose $TMP_NMT $TMP_EDIT | fstcompose - $TMP_HIFST | fstprune --nstate=100000 | fstprint | awk '{if ($3 == 999999998) $3=$4; print $0}' | fstcompile --arc_type=tropicalsparsetuple | fstproject | gzip -c > $TMP_COMPOSED
  if [ -z "$out_n_best" ]; then
    cp $TMP_COMPOSED $trgt_dir/$id.fst.gz
  else
    # We store it first in TMP_HIFST because we do not want the output file to show up too early $out_n_best
    zcat $TMP_COMPOSED | fstshortestpath --unique --nshortest=750 | fstrmepsilon | fstshortestpath --unique --nshortest=100 | fstrmepsilon | fstdeterminize | fstminimize | gzip -c > $TMP_HIFST
    cp $TMP_HIFST $trgt_dir/$id.fst.gz
  fi
done

unset TUPLEARC_WEIGHT_VECTOR

rm $TMP_UNK
rm $TMP_UNK_TXT
rm $TMP_REPLACE
rm $TMP_HIFST
rm $TMP_NMT_PRE
rm $TMP_NMT
rm $TMP_VOCAB_HIFST
rm $TMP_VOCAB_NMT
rm $TMP_EDIT
rm $TMP_EDIT_TXT
rm $TMP_COMPOSED
