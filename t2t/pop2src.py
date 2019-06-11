# coding=utf-8
r"""Replaces OSM POP operations with the source words."""

import argparse
import sys

parser = argparse.ArgumentParser(description='POP -> source word replacement.')
parser.add_argument('-s','--source', help='Source sentences.', required=True)
args = parser.parse_args()

SRC_POP = "4"

with open(args.source) as src_reader:
  for src_words, org_ops in zip(src_reader, sys.stdin):
    src_words = src_words.strip().split()
    ops = []
    pos = 0
    for op in org_ops.strip().split():
      if op == SRC_POP:
        ops.append(src_words[pos])
        pos += 1
      else:
        ops.append(op)
    print(" ".join(ops))

