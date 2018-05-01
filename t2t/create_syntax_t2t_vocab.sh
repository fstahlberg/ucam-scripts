#!/bin/bash

if [ $# -ne 2 ]; then
  echo "Usage: ../scripts/create_syntax_t2t_vocab.sh <format> <tag-file>"
  echo "  Creates a list of vocabulary entries for syntactic annotations"
  echo "  which can be appended to the normal T2T vocabulary list."
  echo "    <format>: layerbylayer, layerbylayer_pop, flat_starttagged, flat_endtagged, flat_bothtagged"
  echo "    <tag-file>: Path to a plain text file with all possible tags"
  exit 1;
fi

tag_file=$2
case "$1" in
'layerbylayer')
  cat $tag_file | awk "{print \"'##\"\$0\"##'\";}"
;;
'layerbylayer_pop')
  cat $tag_file | awk "{print \"'##\"\$0\"##'\";}"
  echo "'##POP##'"
;;
'flat_starttagged')
  cat $tag_file | awk "{print \"'##(\"\$0\"##'\";}"
  echo "'##)##'"
;;
'flat_endtagged')
  cat $tag_file | awk "{print \"'##\"\$0\")##'\";}"
  echo "'##(##'"
;;
'flat_bothtagged')
  cat $tag_file | awk "{print \"'##(\"\$0\"##'\"; print \"'##\"\$0\")##'\";}"
;;
esac

