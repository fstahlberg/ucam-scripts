#!/bin/bash
# This script aims to fix issues related to NMT decoding of surnames
# when the source side is lower cased. Normally, HiFST is better in
# dealing with surnames and NMT tends to translate them. To fix this,
# we force HiFST lattices to contain a certain word if it has occurred
# in both the source sentence and the first best translation of HiFST.
# This script creates the constraint lattices. The full procedure is:
#
# 1.) Get shortest path from HiFST lattice
# 2.) Collect all words in the lattice vocab. that occurr in the source sentence
# 3.) Filter this list by short_list
# 3.) For each of these words, create an acceptor which accepts a sequence if it contains this word
# 4.) Compose all new acceptors and the lattice

if [ $# -ne 4 ]; then
  echo "Usage: ./create_name_constraint_fst_directory.sh <src_directory> <trgt_directory> <src-sentences> <match_pairs>"
  echo "  Constraints lattices to contain pass-through words."
  echo "    <src_directory>: directory containing lattices with log arcs (see create_fst_directory.sh)"
  echo "    <trgt_directory>: directory to write the converted lattice"
  echo "    <src-sentences>: Source sentences (indexed)"
  echo "    <match_pairs>: File containing pairs of word indices "src_word_idx trg_word_idx" defining the word indices"
  echo "                   which represent the same word in the different wmaps"
  exit 1;
fi

source $(dirname $0)/import_hifst_environment.sh
mkdir -p $2
src_sens=$3
match_pairs=$4

TMP_PREFIX="tmp"
cut -d' ' -f1 $match_pairs | sort -u > $TMP_PREFIX.match.vcb

for src_lat in $(ls $1/*.fst)
do
  trgt_lat=$2/$(basename $src_lat)

  cat $src_lat | fstmap --map_type=to_standard | fstarcsort > $TMP_PREFIX.fst
  src_sen=$(head -n $(basename $src_lat .fst) $src_sens | tail -n 1)
  echo $src_sen | tr ' ' "\n" | sort -u > $TMP_PREFIX.src.vcb
  cat $src_lat | fstmap --map_type=to_standard | printstrings.O2.bin --semiring=stdarc | tr ' ' "\n" | sort -u | egrep '^[0-9]+$' > $TMP_PREFIX.1best.vcb
  fstprint $src_lat | cut -f3 | sort -g -u > $TMP_PREFIX.lat.vcb
  for src_word in $(cat $TMP_PREFIX.match.vcb $TMP_PREFIX.src.vcb | sort | uniq -c | awk '{if ($1 > 1) print $2}')
  do
    egrep "^$src_word " $match_pairs | cut -d' ' -f2- > $TMP_PREFIX.matched.vcb
    for trg_word in $(cat $TMP_PREFIX.matched.vcb $TMP_PREFIX.1best.vcb | sort | uniq -c | awk '{if ($1 > 1) print $2}')
    do
        echo "Lat $src_lat: Build acceptor for $src_word - $trg_word"
        cat $TMP_PREFIX.lat.vcb | awk '{print "0 0 "$1" "$1"\n1 1 "$1" "$1}END{print "0 1 '$trg_word' '$trg_word'\n1"}' > $TMP_PREFIX.name.fst.txt
        cat $TMP_PREFIX.name.fst.txt | fstcompile | fstarcsort > $TMP_PREFIX.name.fst
        fstcompose $TMP_PREFIX.fst $TMP_PREFIX.name.fst | fstdeterminize | fstminimize | fstarcsort > $TMP_PREFIX.new.fst
        cp $TMP_PREFIX.new.fst $TMP_PREFIX.fst
    done
  done
  cat $TMP_PREFIX.fst | fstmap -map_type=to_log | fstpush --push_weights > $trgt_lat
done

rm $TMP_PREFIX.match.vcb $TMP_PREFIX.fst $TMP_PREFIX.src.vcb $TMP_PREFIX.lat.vcb $TMP_PREFIX.1best.vcb $TMP_PREFIX.new.fst
