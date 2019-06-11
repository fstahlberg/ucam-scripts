# coding=utf-8
r"""Reinserts SRC_POP after preordering."""

import argparse
import sys

parser = argparse.ArgumentParser(description='Inserts delimiter symbols into lines in stdin. Distance between delimiters specified via -f.')
parser.add_argument('-f','--fertilities', help='Desired segment lengths.', required=True)
parser.add_argument('-d','--delimiter', help='Delimiter symbol.', default='4')
args = parser.parse_args()

with open(args.fertilities) as fert_reader:
  for fert_line, input_line in zip(fert_reader, sys.stdin):
    words = input_line.strip().split()
    idx = 0
    out = []
    for fert in map(int, fert_line.strip().split()):
      for _ in xrange(fert):
        out.append(words[idx])
        idx += 1
      out.append(args.delimiter)
    print(" ".join(out))

