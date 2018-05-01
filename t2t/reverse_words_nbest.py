# coding=utf-8
r"""Reverse words in a nbest list."""

import sys

for line in sys.stdin:
  parts = line.strip().split("|")
  words = parts[3].strip().split()
  words.reverse()
  parts[3] = " %s " % ' '.join([w for w in words])
  print('|'.join(parts))

