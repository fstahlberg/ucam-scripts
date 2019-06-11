# coding=utf-8
r"""Extracts vocabulary by sentence from an n-best list."""

import argparse
import sys

parser = argparse.ArgumentParser(description='Extracts vocab by sentence from an n-best.')
args = parser.parse_args()

prev_id = "0"
words = []
for line in sys.stdin:
  parts = line.split("|||")
  cur_id = parts[0].strip()
  if cur_id != prev_id:
    print(" ".join(sorted(set(words))))
    words = []
    prev_id = cur_id
  words.extend(parts[1].strip().split())

print(" ".join(sorted(set(words))))
