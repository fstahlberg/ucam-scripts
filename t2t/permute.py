# coding=utf-8
r"""Permutes elements in each line of stdin."""

import argparse
import sys

parser = argparse.ArgumentParser(description='Permutes words in stdin.')
parser.add_argument('-p','--permutations', help='Text file with permutations with as many line as stdin.', required=True)
args = parser.parse_args()

with open(args.permutations) as perm_reader:
  for perm_line, input_line in zip(perm_reader, sys.stdin):
    perm = map(int, perm_line.strip().split())
    words = input_line.strip().split()
    permuted = [words[p] for p in perm]
    print(" ".join(permuted))

