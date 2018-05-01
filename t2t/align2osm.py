# coding=utf-8
r"""Converts alignments to operation sequences. The format of the alignments is:
i1 j1 i2 j2 i3 j3 ... iK jK

where i/j are positions of the src/trg sentences, starting at 0.

The operation sequence model is similar to

https://www.mitpressjournals.org/doi/pdf/10.1162/COLI_a_00218

but the operations are defined slightly differently. Our OSM knows the following
control signals:

EOP: End of phrase: Shift to the next source symbol.
GAP: Insert a target side gap.
JUMP_FWD: Jump one gap forward.
JUMP_BWD: Jump one gap backward.

Alignments are cleaned from alignment links which do not fit into this model:

- If one target word is aligned to multiple source words, we only keep the first
  alignment link.
- If a target word is not aligned to any source word, copy the alignment information 
  from the preceeding target word. If we are at sentence begin, copy it from the
  following target word.
"""

import logging
import argparse
import sys

parser = argparse.ArgumentParser(description='Converts alignments to OSM sequences.')
parser.add_argument('-s','--source', help='Source sentences.', required=True)
parser.add_argument('-t','--target', help='Target sentences.', required=True)
parser.add_argument('-a','--alignments', help='Alignments.', required=True)
args = parser.parse_args()

def compile_ops_jump(compiled, head, step):
  head += step
  while compiled[head] != "X":
    head += step
  return head

def compile_ops_insert(compiled, head, op):
  compiled = compiled[:head] + [op] + compiled[head:]
  head += 1
  return head, compiled

def compile_ops(ops):
  compiled = ["X"]
  src_pos = 0
  head = 0
  for op in ops:
    if op == "EOP":
      src_pos += 1
    elif op == "GAP":
      head, compiled = compile_ops_insert(compiled, head, "X")
    elif op == "JUMP_FWD":
      head = compile_ops_jump(compiled, head, 1)
    elif op == "JUMP_BWD":
      head = compile_ops_jump(compiled, head, -1)
    else:
      head, compiled = compile_ops_insert(compiled, head, "%s(%d)" % (op, src_pos))
  return "%s (head: %d)" % (" ".join(compiled), head)
    
def preprocess_alignment(al_links, trg_len):
  al_links.sort(key=lambda x: (x[1], -x[0]))  # Sort ascending by target pos
  trg2src = [-1 for _ in xrange(trg_len)]
  for src_pos, trg_pos in al_links:
    if trg2src[trg_pos] == -1:
      trg2src[trg_pos] = src_pos
  # Align unaligned target words
  prev_src_pos = al_links[0][0]
  for trg_pos in xrange(trg_len):
    if trg2src[trg_pos] == -1:
      trg2src[trg_pos] = prev_src_pos
    prev_src_pos = trg2src[trg_pos]
  clean_al_links = [(src_pos, trg_pos) for trg_pos, src_pos in enumerate(trg2src)]
  return clean_al_links

def get_hole_idx(holes, trg_pos):
  # binary search asymptotically faster, but we don't expect to have more
  # than 10 holes or so anyway, so screw it.
  # We also assume that there is in fact a hole for trg_pos
  for idx, (start, end) in enumerate(holes):
    if end >= start and end >= trg_pos:
      return idx

def insert_hole(holes, hole):
  holes.append(hole)
  holes.sort()

def generate_operations(src, trg, src2trg):
  holes = [(0, 1000000)] # (start_idx, end_idx) of holes, both inclusive
  ops = []
  head = 0 # hole index
  for src_pos, (src_word, trg_positions) in enumerate(zip(src, src2trg)):
    for trg_pos in trg_positions:
      hole_idx = get_hole_idx(holes, trg_pos)
      #print("move head from %d to %d" % (head, hole_idx))
      # Move head to the right hole
      if head > hole_idx:
        incr = -1
        op = "JUMP_BWD"
      else:
        incr = 1
        op = "JUMP_FWD"
      while hole_idx != head:
        ops.append(op)
        head += incr
      if holes[head][0] != trg_pos: # Need to insert a new hole before
        insert_hole(holes, (holes[head][0], trg_pos-1))
        ops.append("GAP")
        head += 1
      ops.append(trg[trg_pos])
      holes[head] = (trg_pos + 1, holes[head][1])
    ops.append("EOP")
    #print("\nEnd of phrase %d (%s) -> %s" % (src_pos, src_word, trg_positions))
    #print(holes)
    #print("%s (op_head: %d)" % (" ".join(ops), head))
    #print(compile_ops(ops))
  return ops

with open(args.source) as src_reader:
  with open(args.target) as trg_reader:
    with open(args.alignments) as al_reader:
      sen_idx = 0
      for src, trg, al in zip(src_reader, trg_reader, al_reader):
        #print("\n SENTENCE %d -------------------------" % sen_idx)
        sen_idx += 1
        #print(src)
        #print(trg)
        #print(al)
        src = src.strip().split()
        trg = trg.strip().split()
        al = map(int, al.strip().split())
        al_links = [(al[i], al[i+1]) for i in xrange(0, len(al), 2)]
        #print(al_links)
        al_links = preprocess_alignment(al_links, len(trg))
        al_links.sort(key=lambda x: x[1])  # Sort ascending by target pos
        src2trg = [[] for _ in xrange(len(src))]
        for src_pos, trg_pos in al_links:
          src2trg[src_pos].append(trg_pos)
        #print([bla for bla in enumerate(src2trg)])
        ops = generate_operations(src, trg, src2trg)
        print(" ".join(ops))


