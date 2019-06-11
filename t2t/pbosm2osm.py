# coding=utf-8
r"""Transformes a phrase-based OSM sequence to a token-based OSM sequence, keeps phrases together."""

import argparse
import sys

parser = argparse.ArgumentParser(description='PBOSM -> OSM conversion.')
args = parser.parse_args()

SRC_POP1 = "4"
SRC_POP2 = "8"

for pbosm in sys.stdin:
  pbosm = pbosm.strip().split()
  osm = []
  pop2_cnt = 0
  for op in pbosm:
    if op == SRC_POP2:
      pop2_cnt += 1
    elif op == SRC_POP1:
      osm.extend([SRC_POP1] * (pop2_cnt + 1))
      pop2_cnt = 0
    else:
      osm.append(op)
  osm.extend([SRC_POP1] * pop2_cnt)
  print(" ".join(osm))

