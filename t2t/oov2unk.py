# coding=utf-8
r"""Replaces word IDs equal or larger than the vocab size with the UNK id."""

import argparse
import sys

parser = argparse.ArgumentParser(description='Replaces word IDs equal or larger than the vocab size with the UNK id.')
parser.add_argument('-v','--vocab_size', help='Vocabulary size.', type=int, required=True)
parser.add_argument('-u','--unk_id', help='UNK ID (default: T2T UNK).', required=False, default=3)
args = parser.parse_args()

for line in sys.stdin:
  ids = [int(w) for w in line.strip().split()]
  print(" ".join(map(str, [i if i < args.vocab_size else args.unk_id for i in ids])))

