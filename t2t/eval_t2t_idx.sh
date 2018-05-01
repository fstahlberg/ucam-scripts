#!/bin/bash

if [ $# -ne 2 ] && [ $# -ne 3 ]; then
  echo "Usage: ../scripts/eval_t2t_idx.sh <vocab-file> <raw-ref-file> [<lang>] < indexed-hypos"
  echo "  BLEU evaluation script from tensor2tensor for indexed input."
  echo "    <vocab-file>: T2T vocabulary file"
  echo "    <raw-ref-file>: Tokenized reference file"
  echo "    <lang>: Target language (default: de)"
  exit 1;
fi


# Usage: cat bla | eval_t2t_idx.sh <vocab_file> <raw_ref_file> <lang>
cat /dev/stdin  | python $(dirname $0)/apply_t2t_preprocessing.py --vocab_file $1 | $(dirname $0)/eval_t2t.sh /dev/stdin $2 $3
