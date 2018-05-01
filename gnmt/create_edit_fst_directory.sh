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
MAX_HIFST_STATES=500000

if [ $# -ne 9 ] && [ $# -ne 10 ] && [ $# -ne 11 ]; then
  echo "Usage: ./create_fst_directory.sh <hifst_directory> <nmt_directory> <trgt_directory> <range> <nmt-vocab> <nmt-scale> <edit-cost> <ins-unk-cost> <unk-to-in-vocab> [out-n-best [max-unk-mult]]"
  echo "  Creates a FST with scores from HiFST and NMT."
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

source $(dirname $0)/import_hifst_environment.sh
hifst_dir=$1
nmt_dir=$2
trgt_dir=$3
range=$4
nmt_vocab=$5
nmt_scale=$6
edit_cost=$7
unk_cost=$8
unk_to_in_vocab_cost=$9
out_n_best=${10}
max_unk_mult=${11}
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

# Create UNK replacement FST
rm $TMP_UNK_TXT
if [ -z "$max_unk_mult" ]; then
  # Unlimited number of unk multiplications
  echo "0 1 $UNK_ID $UNK_ID" >> $TMP_UNK_TXT
  echo "1 1 $UNK_ID $UNK_ID $unk_cost" >> $TMP_UNK_TXT
  echo "1" >> $TMP_UNK_TXT
else
  # Limited number of unk multiplications: left-to-right topology with skip connections to final state
  prev_state=0
  for state in $(seq 1 $(echo "$max_unk_mult-1" | bc))
  do
    echo "$prev_state $state $UNK_ID $UNK_ID $unk_cost" >> $TMP_UNK_TXT
    echo "$prev_state $max_unk_mult $UNK_ID $UNK_ID" >> $TMP_UNK_TXT
    prev_state=$state
  done
  echo "$prev_state $max_unk_mult $UNK_ID $UNK_ID" >> $TMP_UNK_TXT
  echo "$max_unk_mult" >> $TMP_UNK_TXT
fi
fstcompile $TMP_UNK_TXT | fstarcsort --sort_type=olabel > $TMP_UNK

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
    zcat $hifst_lat | fstmap --map_type=to_standard | fstprune --nstate=$MAX_HIFST_STATES | fstrmepsilon | fstdeterminize | fstminimize | fstarcsort --sort_type=olabel > $TMP_HIFST
  else
    cat $hifst_lat | fstmap --map_type=to_standard | fstprune --nstate=$MAX_HIFST_STATES | fstrmepsilon | fstdeterminize | fstminimize | fstarcsort --sort_type=olabel > $TMP_HIFST
  fi
  if [[ $nmt_lat == *.gz ]]; then
    zcat $nmt_lat | fstrelabel --relabel_ipairs=$TMP_REPLACE --relabel_opairs=$TMP_REPLACE | fstprint |  awk '{if (NF != 5) print $0; else print $1"\t"$2"\t"$3"\t"$4"\t"($5*'$nmt_scale')} ' | fstcompile > $TMP_NMT_PRE
  else
    cat $nmt_lat | fstrelabel --relabel_ipairs=$TMP_REPLACE --relabel_opairs=$TMP_REPLACE | fstprint |  awk '{if (NF != 5) print $0; else print $1"\t"$2"\t"$3"\t"$4"\t"($5*'$nmt_scale')} ' | fstcompile > $TMP_NMT_PRE
  fi
  # Following operations on the NMT lattice
  # 1.) Replace UNK ids with REPLACE ID
  # 2.) Replace REPLACE ID with the UNK FST which accepts a single UNK token and additional UNK tokens at cost unk_cost
  # 3.) remove epsilon, determinize, minimize
  # 4.) scale the weights
  # 5.) arc sort to make fstcompose work
  fstreplace --epsilon_on_replace $TMP_NMT_PRE $ROOT_ID $TMP_UNK $REPLACE_ID | fstrmepsilon | fstdeterminize | fstminimize | fstarcsort --sort_type=olabel > $TMP_NMT
  fstprint $TMP_HIFST | cut -f3 | sort -g -u > $TMP_VOCAB_HIFST
  fstprint $TMP_NMT | cut -f3 | sort -g -u | egrep -v "^$UNK_ID$" > $TMP_VOCAB_NMT

  # Create edit distance transducer
  rm $TMP_EDIT_TXT
  echo "0 0 $UNK_ID 0 $edit_cost" >> $TMP_EDIT_TXT
  for nmt_word in $(cat $TMP_VOCAB_NMT)
  do # Deletions
    echo "0 0 $nmt_word 0 $edit_cost" >> $TMP_EDIT_TXT 
  done
  for hifst_word in $(cat $TMP_VOCAB_HIFST)
  do # unk substitution (for free) and insertions
    echo "0 0 0 $hifst_word $edit_cost" >> $TMP_EDIT_TXT
    if [[ "$hifst_word" -gt "$nmt_vocab" ]];
    then
      echo "0 0 $UNK_ID $hifst_word" >> $TMP_EDIT_TXT
    else
      echo "0 0 $UNK_ID $hifst_word $unk_to_in_vocab_cost" >> $TMP_EDIT_TXT
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
        echo "0 0 $nmt_word $hifst_word $edit_cost" >> $TMP_EDIT_TXT
      fi
    done
  done
  echo "0" >> $TMP_EDIT_TXT
  fstcompile $TMP_EDIT_TXT | fstarcsort --sort_type=olabel > $TMP_EDIT

  # Compose to final FST
  fstcompose $TMP_NMT $TMP_EDIT | fstcompose - $TMP_HIFST | gzip -c > $TMP_COMPOSED
  if [ -z "$out_n_best" ]; then
    cp $TMP_COMPOSED $trgt_dir/$id.fst.gz
  else
    zcat $TMP_COMPOSED | fstshortestpath --nshortest=$out_n_best | gzip -c > $trgt_dir/$id.fst.gz
  fi
done

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
