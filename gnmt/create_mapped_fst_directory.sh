#!/bin/bash
# Transforms lattices from one wmap to another

if [ $# -ne 3 ] && [ $# -ne 4 ]; then
  echo "Usage: ./create_mapped_fst_directory.sh <src_directory> <trgt_directory> <inv-idxmap> [<range>]"
  echo "  Applies fstrelabel to a lattice directory and converts it to standard arc type."
  echo "    <src_directory>: lattice directory containing lattice files with original word indices"
  echo "    <trgt_directory>: directory to write the converted lattices"
  echo "    <inv-idxmap>: Word index pairs in the reverse direction"
  echo "    <range>: Index range. Format: <from-idx>:<to-idx> (both inclusive)"
  exit 1;
fi

source $(dirname $0)/import_hifst_environment.sh
mkdir -p $2
range=$4

TMP_FILE=$(tempfile)
cat $3 | awk '{print $2" "$1}' > $TMP_FILE

if [ -z "$range" ]; then
  ids=$(ls $1/*.fst* | xargs -n 1 basename | cut -d'.' -f1 | sort -g)
else
  ids=$(seq $(echo $range | cut -d':' -f1) $(echo $range | cut -d':' -f2))
fi

for id in $ids
do
  src_lat=$(ls $1/$id.fst*)
  if [[ $src_lat == *.gz ]]; then
    zcat $src_lat | fstrelabel -relabel_ipairs=$TMP_FILE -relabel_opairs=$TMP_FILE | fstmap --map_type=to_standard | gzip -c > $2/$id.fst.gz
  else
    cat $src_lat | fstrelabel -relabel_ipairs=$TMP_FILE -relabel_opairs=$TMP_FILE | fstmap --map_type=to_standard > $2/$id.fst 
  fi
done

rm $TMP_FILE
