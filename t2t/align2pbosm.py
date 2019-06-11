# coding=utf-8
r"""Converts alignments to phrase-based operation sequences. The format of the alignments is:
i1 j1 i2 j2 i3 j3 ... iK jK

where i/j are positions of the src/trg sentences, starting at 0.

The operation sequence model is similar to

https://arxiv.org/abs/1808.09688

but uses two source side read heads. The available operations are:

SRC_POP1: Move ReadHead1 by one to the right
SET_MARKER: Insert a marker
JUMP_FWD: Jump one marker forward.
JUMP_BWD: Jump one marker backward.
SRC_POP2: Move ReadHead1 by one to the right and move ReadHead2 to ReadHead1's new position

"""

import logging
import argparse
import sys
import numpy as np

parser = argparse.ArgumentParser(description='Converts alignments to OSM sequences.')
parser.add_argument('-s','--source', help='Source sentences.', required=True)
parser.add_argument('-t','--target', help='Target sentences.', required=True)
parser.add_argument('-a','--alignments', help='Alignments.', required=True)
parser.add_argument('-v','--verbose', help='Debug mode.', default=False, action="store_true")
parser.add_argument('-f','--fill_source', help='If true, also align unaligned source tokens.', default=False, action="store_true")
parser.add_argument('-r','--restrict_marker', help='If true, SET_MARKER operations are not allowed after words (only after JUMPs and POPs).', 
                    default=False, action="store_true")
parser.add_argument('-m','--wmap', help='If set, load this subword-wmap and make sure that phrase boundaries only occur at word boundaries.', default="")
args = parser.parse_args()

COST_TOLERANCE = 0.1

def fill_trg_gaps(al_mat, orientation="cols"):
  col_is_empty = np.sum(al_mat, axis=0) == 0
  n_rows, n_cols = al_mat.shape
  start_col = 0
  while start_col < n_cols:
    if col_is_empty[start_col]:
      fill_col = np.zeros(n_rows, np.int) if start_col == 0 else np.copy(al_mat[:, start_col - 1])
      end_col = start_col + 1
      while end_col < n_cols and col_is_empty[end_col]:
        end_col += 1
      if end_col < n_cols:
        fill_col = np.clip(fill_col + al_mat[:, end_col], 0, 1)
      for col in xrange(start_col, end_col):
        al_mat[:, col] = fill_col
      if args.verbose:
        print("Filling up %s %d to %d with %s" % (orientation, start_col, end_col, fill_col))
      start_col = end_col
    else:
      start_col += 1


class Node(object):

  def __init__(self, row1, col1, row2, col2):
    self.row1 = row1
    self.col1 = col1
    self.row2 = row2
    self.col2 = col2
    self.children = []

  def is_leaf(self):
    return not bool(self.children)

  def fill_mat(self, al_mat):
    if self.is_leaf():
      al_mat[self.row1:self.row2, self.col1:self.col2] = 1
    else:
      for c in self.children:
        c.fill_mat(al_mat)

  def compute_cost(self, split_row, al_mat):
    if split_row <= self.row1 or split_row >= self.row2:
      return 0.0
    if not self.is_leaf():
      return sum(c.compute_cost(split_row, al_mat) for c in self.children)
    # This is a leaf which covers the split row: compute cost
    upper = np.sum(al_mat[self.row1:split_row, self.col1:self.col2], axis=0)
    lower = np.sum(al_mat[split_row:self.row2, self.col1:self.col2], axis=0)
    if args.restrict_marker:
      abs_cost = min(
          np.min(self._single_split_cost_array(upper, lower)), 
          np.min(self._single_split_cost_array(lower, upper)))
    else:
      abs_cost = np.sum(np.min([upper, lower], axis=0))
    return float(abs_cost) / float((self.row2 - self.row1) * (self.col2 - self.col1))

  def _single_split_cost_array(self, first, second):
      first_cumsum = np.concatenate([[0], np.cumsum(first[::-1])])[::-1]
      second_cumsum = np.concatenate([[0], np.cumsum(second)])
      return first_cumsum + second_cumsum
 
  def split(self, split_row, al_mat):
    if split_row <= self.row1 or split_row >= self.row2:
      return 
    if not self.is_leaf():
      for c in self.children:
        c.split(split_row, al_mat)
      return
    # This is a leaf which covers the split row
    if args.restrict_marker:
      return self._split_restricted(split_row, al_mat)
    else:
      return self._split_unrestricted(split_row, al_mat)

  def _split_restricted(self, split_row, al_mat):
    upper = np.sum(al_mat[self.row1:split_row, self.col1:self.col2], axis=0)
    lower = np.sum(al_mat[split_row:self.row2, self.col1:self.col2], axis=0)
    uplo_costs = self._single_split_cost_array(upper, lower)
    loup_costs = self._single_split_cost_array(lower, upper)
    pos = np.argmin(np.concatenate([uplo_costs, loup_costs]))
    uplo = True
    if pos >= len(uplo_costs):
      uplo = False
      pos %= len(uplo_costs)
    if pos > 0:
      first_child = Node(self.row1, self.col1, split_row, self.col1 + pos)
      if not uplo:
        first_child.row1 = split_row
        first_child.row2 = self.row2
      self.children.append(first_child)
    if self.col1 + pos < self.col2:
      second_child = Node(self.row1, self.col1 + pos, split_row, self.col2)
      if uplo:
        second_child.row1 = split_row
        second_child.row2 = self.row2
      self.children.append(second_child)

  def _split_unrestricted(self, split_row, al_mat):
    upper = np.sum(al_mat[self.row1:split_row, self.col1:self.col2], axis=0)
    lower = np.sum(al_mat[split_row:self.row2, self.col1:self.col2], axis=0)
    all_use_upper = upper >= lower
    prev_use_upper = not all_use_upper[0]
    cur_child = Node(0, 0, 0, 0)
    for offset, use_upper in enumerate(all_use_upper):
      if use_upper == prev_use_upper:
        cur_child.col2 = self.col1 + offset + 1
      else:
        cur_child = Node(self.row1, self.col1 + offset, split_row, self.col1 + offset + 1)
        if not use_upper:
          cur_child.row1 = split_row
          cur_child.row2 = self.row2
        self.children.append(cur_child)
        prev_use_upper = use_upper

  def print_tree(self, level=0):
      print("%s [%d:%d, %d:%d]" % (" |" * level, self.row1, self.row2, self.col1, self.col2))
      for c in self.children:
        c.print_tree(level + 1)

      
def subdivide(root, al_mat, src):
  visited = set()
  if no_split_tokens:
    for src_pos, src_token in enumerate(src):
      if src_token in no_split_tokens:
        visited.add(src_pos + 1)
  while len(visited) < root.row2 - root.row1:
    best_cost = 1000000.0
    for split_row in xrange(root.row1 + 1, root.row2):
      if split_row in visited:
        continue
      cost = root.compute_cost(split_row, al_mat)
      if cost < best_cost:
        best_cost = cost
        best_row = split_row
        if cost <= 0.0000001:
          break
    if best_cost < COST_TOLERANCE:
      if args.verbose:
        print("Splitting tree at row %d with cost %f" % (best_row, best_cost))
      root.split(best_row, al_mat)
      visited.add(best_row)
    else:
      break
    
# OSM generation
    
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

def generate_operations(trg, src2trg, fertilities):
  holes = [(0, 1000000)] # (start_idx, end_idx) of holes, both inclusive
  ops = []
  head = 0 # hole index
  for src_pos, (trg_positions, fertility) in enumerate(zip(src2trg, fertilities)):
    for _ in xrange(1, fertility):
      ops.append("SRC_POP2")
    for trg_pos in trg_positions:
      hole_idx = get_hole_idx(holes, trg_pos)
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
        ops.append("SET_MARKER")
        head += 1
      ops.append(trg[trg_pos])
      holes[head] = (trg_pos + 1, holes[head][1])
    ops.append("SRC_POP1")
  return ops

no_split_tokens = set()
if args.wmap:
  with open(args.wmap) as wmap_reader:
    for wmap_line in wmap_reader:
      txt, idx = wmap_line.strip().split()
      if not "</w>" in txt:
        no_split_tokens.add(idx)

with open(args.source) as src_reader:
  with open(args.target) as trg_reader:
    with open(args.alignments) as al_reader:
      sen_idx = 0
      for src, trg, al in zip(src_reader, trg_reader, al_reader):
        if args.verbose:
          print("\nSENTENCE %d" % sen_idx)
          print("-----------------------")
        sen_idx += 1
        src = src.strip().split()
        trg = trg.strip().split()
        al = map(int, al.strip().split())
        if not al:
          al = [0, 0]
        al_mat = np.zeros((len(src), len(trg)), np.int)
        for i in xrange(0, len(al), 2):
          al_mat[al[i], al[i+1]] = 1
        org_al_mat = np.copy(al_mat)
        if args.verbose:
          print("Original:")
          print(al_mat)
        fill_trg_gaps(al_mat)
        if args.fill_source:
          al_mat_t = np.transpose(al_mat)
          fill_trg_gaps(al_mat_t, orientation="rows")
          al_mat = np.transpose(al_mat_t)
        if args.verbose:
          print("Filled gaps:")
          print(al_mat)
        root = Node(0, 0, len(src), len(trg))
        subdivide(root, al_mat, src)
        al_mat *= 0
        root.fill_mat(al_mat)
        if args.verbose:
          print("Phrase tree:")
          root.print_tree()
          print("After phrase segmentation:")
          print(al_mat)
          print("Total error: %d" % np.sum(np.abs(org_al_mat - al_mat)))
        src2trg = []
        fertilities = []
        prev_row = -1
        for row in al_mat:
          if all(row == prev_row):
            fertilities[-1] += 1
          else:
            src2trg.append(list(np.nonzero(row)[0]))
            fertilities.append(1)
            prev_row = row
        if args.verbose:
          print("Links: %s" % ", ".join("%s (fert: %d)" % (m, f) for m, f in zip(src2trg, fertilities)))
          print("SRC: %s" % ' '.join(src))
          print("TRG: %s" % ' '.join(trg))
          print("Final OSM sequence:")
        ops = generate_operations(trg, src2trg, fertilities)
        print(" ".join(ops))

