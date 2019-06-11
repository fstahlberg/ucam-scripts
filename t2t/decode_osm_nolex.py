# coding=utf-8
r"""Uses an operation sequence without lexical translations to reorder
the source sentence to be in target word order.

We use the same operation set as align2osm.py.
"""

import logging
import argparse
import sys
import re

parser = argparse.ArgumentParser(description='Reorders source words to target word order using a non-lexical OSM sequence.')
parser.add_argument('-f','--format', default='plain', help='plain, incremental, perm')
parser.add_argument('-s','--source', required=True, help='Source sentences')
args = parser.parse_args()

EOP = ["4", "<EOP>"]
GAP = ["5", "<GAP>"]
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

def compile_ops(ops, src_words, idx, output_format):
  if output_format == "incremental":
    print("\nSentence %d -----------------------------" % idx)
  compiled = ["X"]
  src_pos = 0
  head = 0
  for op in ops:
    if op in EOP:
      head, compiled = compile_ops_insert(compiled, head, "%s(%d)" % (src_words[src_pos], src_pos))
      src_pos += 1
    elif op in GAP:
      head, compiled = compile_ops_insert(compiled, head, "X")
    elif op in JUMP_FWD:
      head = compile_ops_jump(compiled, head, 1)
    elif op in JUMP_BWD:
      head = compile_ops_jump(compiled, head, -1)
    elif output_format == "incremental":
      print("Illegal operation '%s'" % op)
    if output_format == "incremental":
      print("After %s: %s (head: %d)" % (op, " ".join(compiled), head))
  without_x = [s for s in compiled if s != "X"]
  plain =  " ".join([re.sub(r"\([0-9]+\)$", "", s) for s in without_x])
  perm = " ".join([re.sub(r"^[0-9]+\(([0-9]+)\)$", r"\1", s) for s in without_x])
  if output_format == "plain":
    print(plain)
  elif output_format == "perm":
    print(perm)
  elif output_format == "incremental":
    print("OSM: %s" % ' '.join(ops))
    print("Original:  %s" % ' '.join(src_words))
    print("Reordered: %s" % plain)
    print("Permutation: %s" % perm)


with open(args.source) as src_reader:
  for idx, (src_line, osm_line) in enumerate(zip(src_reader, sys.stdin)):
    ops = osm_line.strip().split()
    src_words = src_line.strip().split()
    compile_ops(ops, src_words, idx, args.format)

