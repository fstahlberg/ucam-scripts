#!/bin/bash

export LC_ALL=en_GB.utf8

if [ $# -ne 2 ]; then
  echo "Usage: ../scripts/remove_pop_from_t2t_dataset.sh <src-prefix> <trg-prefix>"
  echo "  Creates training data for syntax-based layer-by-layer models."
  echo "    <src-prefix>: Dataset without syntactic annotations (we read <src-prefix>-[dev|train]-*-of-*)"
  echo "    <trg-prefix>: Target dataset (we write <trg-prefix>-[dev|train]-*-of-*)"
  exit 1;
fi

src_prefix=$1
trg_prefix=$2
src_vocab=$(dirname $src_prefix)"/vocab."$(basename $src_prefix)
trg_vocab=$(dirname $trg_prefix)"/vocab."$(basename $trg_prefix)

# Copy dev set
for src_file in $(ls $src_prefix-dev-*)
do
  trg_file=$trg_prefix-dev-$(echo $src_file | sed 's/^.*-dev-//')
  echo "-> Copy $src_file to $trg_file"
  cp $src_file $trg_file
done

# Create vocabulary
echo "-> Copy vocabulary file $src_vocab to $trg_vocab"
cp $src_vocab $trg_vocab

# Process train set
for src_file in $(ls $src_prefix-train-*)
do
  trg_file=$trg_prefix-train-$(echo $src_file | sed 's/^.*-train-//')
  echo "-> Converting $src_file to $trg_file"
  python $(dirname $0)/remove_pop_from_t2t_dataset.py --vocab_filename=$trg_vocab --input_filename=$src_file --output_filename=$trg_file
done

