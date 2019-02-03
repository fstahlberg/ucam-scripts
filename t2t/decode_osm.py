# coding=utf-8
r"""Converts operation sequences to plain text, possibly with alignment info.

We use the same operation set as align2osm.py.
"""

import logging
import argparse
import sys
import re

parser = argparse.ArgumentParser(description='Converts OSM sequences to plain text.')
parser.add_argument('-f','--format', default='plain', help='plain, align, pharaoh, parse, fert, incremental')
args = parser.parse_args()

EOP = ["4", "<EOP>", "<SRC_POP1>", "<SRC_POP2>"]
GAP = ["5", "<GAP>", "<SET_MARKER>"]
JUMP_FWD = ["6", "<JUMP_FWD>"]
JUMP_BWD = ["7", "<JUMP_BWD>"]

def compile_ops_jump(compiled, head, step):
  head += step
  while compiled[head] != "X":
    head += step
  return head

def compile_ops_insert(compiled, head, op):
  compiled = compiled[:head] + [op] + compiled[head:]
  head += 1
  return head, compiled

def compile_ops(ops, idx, output_format):
  if output_format == "incremental":
    print("\nSentence %d -----------------------------" % idx)
  compiled = ["X"]
  src_pos = 0
  head = 0
  ferts = [0]
  for op in ops:
    if op in EOP:
      src_pos += 1
      ferts.append(0)
    elif op in GAP:
      head, compiled = compile_ops_insert(compiled, head, "X")
    elif op in JUMP_FWD:
      head = compile_ops_jump(compiled, head, 1)
    elif op in JUMP_BWD:
      head = compile_ops_jump(compiled, head, -1)
    else:
      ferts[src_pos] += 1
      head, compiled = compile_ops_insert(compiled, head, "%s(%d)" % (op, src_pos))
    if output_format == "incremental":
      print("After %s: %s (head: %d)" % (op, " ".join(compiled), head))
  without_x = [s for s in compiled if s != "X"]
  ferts = ferts[:-1]
  if output_format == "parse":
    print("%s (head: %d)" % (" ".join(compiled), head))
  elif output_format == "align":
    print(" ".join(without_x))
  elif output_format == "fert":
    print(" ".join(map(str, ferts)))
  elif output_format == "pharaoh":
    links = [(int(re.search('\(([0-9]+)\)$', s).group(1)), trg_pos)
             for trg_pos, s in enumerate(without_x)]
    print(" ".join("%d-%d" % link for link in sorted(links)))
  elif output_format == "plain":
    print(" ".join([re.sub(r"\([0-9]+\)$", "", s) for s in without_x]))


for idx, line in enumerate(sys.stdin):
  ops = line.strip().split()
  compile_ops(ops, idx, args.format)

