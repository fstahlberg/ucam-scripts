#!/bin/bash

export LC_ALL=en_GB.utf8

if [ $# -ne 2 ] && [ $# -ne 3 ]; then
  echo "Usage: ../scripts/eval_t2t.sh <nbest-file> <svm-model-file> [<exclude-features>]"
  echo "  Reranks an n-best list with libsvm rank."
  echo "    <nbest-file: n-best file in Moses format"
  echo "    <svm-model-file>: SVM file trained with svm-train"
  echo "    <exclude-features>: Passed through to nbest2libsvm.py (default: empty)"
  exit 1;
fi

if [ -z "$3" ]; then
  cat $1 | python $(dirname $0)/nbest2libsvm.py > tmp.svmrank.data
else
  cat $1 | python $(dirname $0)/nbest2libsvm.py -x $3 > tmp.svmrank.data
fi

/data/mifs_scratch/fs439/bin/libsvm-ranksvm-3.22/svm-predict -q tmp.svmrank.data $2 tmp.svmrank.out

paste -d' ' tmp.svmrank.out $1 | sort -g -k1 -r | sort -g -k2 -s | sed 's/^\([0-9e.-]\+\) \(.*\)||| \([0-9e.-]\+\) *$/\2presvm= \3 ||| \1/'


