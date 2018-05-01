#!/bin/bash

export LC_ALL=en_GB.utf8

if [ $# -ne 5 ]; then
  echo "Usage: ../scripts/add_target_syntax_to_t2t_dataset.sh <src-prefix> <trg-prefix> <lang> <terminal-vocab> <format>"
  echo "  Creates training data for syntax-based layer-by-layer models."
  echo "    <src-prefix>: Dataset without syntactic annotations (we read <src-prefix>-[dev|train]-*-of-*)"
  echo "    <trg-prefix>: Target dataset (we write <trg-prefix>-[dev|train]-*-of-*)"
  echo "    <lang>: Target language. 'German', 'English', 'Chinese'"
  echo "    <terminal-vocab>: T2Ts vocabulary file (eg t2t_data/vocab.endefr.32768)"
  echo "    <format>: See add_target_syntax_to_t2t_dataset.py: 'layerbylayer', 'layerbylayer_pop', 'flat_starttagged', 'flat_endtagged', 'flat_bothtagged'"
  exit 1;
fi

source $(dirname $0)/import_t2t_environment_cpu.sh

src_prefix=$1
trg_prefix=$2
lang=$3
terminal_vocab=$4
format=$5
combined_vocab=$(dirname $trg_prefix)"/vocab."$(basename $trg_prefix)

tmp_dir=$(mktemp -d /tmp/add_target_syntax_to_t2t_dataset.XXXXX)
echo "Temp dir: $tmp_dir"

# Create vocabulary
echo "-> Creating vocabulary file $combined_vocab"
cp $terminal_vocab $combined_vocab
$(dirname $0)/create_syntax_t2t_vocab.sh $format /data/mifs_scratch/fs439/exp/t2t/common/stanford/$lang.tags >> $combined_vocab

# Process train set
mkdir -p $tmp_dir
for src_file in $(ls $src_prefix-train-* $src_prefix-dev-*)
do
  trg_file=$trg_prefix-$(echo $src_file | sed 's/^.*-\([traindev]\{3,5\}\)-/\1-/')
  if [ -f $trg_file ]; 
  then
    echo "-> Skipping shard $trg_file (file exists)"
  else
    touch $trg_file
    echo "-> Reading $src_file"
    python $(dirname $0)/inspect_t2t_dataset.py --remove_eos --vocab_filename=$terminal_vocab --input_filename=$src_file --output_field targets > $tmp_dir/out.raw
    echo "-> Parsing $src_file"
    $(dirname $0)/lexparser_std.sh $lang $tmp_dir/out.raw
    echo "Parsed "$(cat $tmp_dir/out.raw.penn.compact | wc -l)" of "$(cat $tmp_dir/out.raw | wc -l)" sentences in $src_file"
    echo "-> Writing $trg_file"
    python $(dirname $0)/add_target_syntax_to_t2t_dataset.py --vocab_filename=$combined_vocab --input_filename=$src_file --penn_filename=$tmp_dir/out.raw.penn.compact --format=$format --output_filename=$trg_file
  fi
done

#rm -r $tmp_dir


