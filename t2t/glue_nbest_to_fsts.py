# coding=utf-8
r"""This script parses an n-best file on the sentence level and generates
document-level FSTs from them by glueing the entries together.
"""

import logging
import argparse
import sys
import os
import pywrapfst as fst
import errno

parser = argparse.ArgumentParser(description='Creates document-level glued FSTs from sentence-level n-best list')
parser.add_argument('-b','--bos_id', help='BOS ID.', required=False, type=int, default=2)
parser.add_argument('-g','--glue_id', help='Glue symbol ID.', required=False, type=int, default=2)
parser.add_argument('-e','--eos_id', help='EOS ID.', required=False, type=int, default=1)

parser.add_argument('-o','--output_dir', help='Output directory.', required=True)
parser.add_argument('-n','--nbest', help='n-best list.', required=True)
parser.add_argument('-s','--src', help='Source sentences (document level).', required=True)
args = parser.parse_args()
logging.getLogger().setLevel(logging.INFO)


def fst_arc(c, from_id, to_id, label, weight=0.0):
  c.write("%d\t%d\t%d\t%d\t%f\n" % (from_id, to_id, label, label, weight))

def fst_finalize(c, last_node, eos_node, path):
  fst_arc(c, last_node, eos_node, args.eos_id)
  c.write("%d\n" % eos_node)
  f = c.compile()
  f.rmepsilon()
  f = fst.determinize(f)
  f.minimize()
  f.topsort()
  f = fst.push(f, push_weights=True)
  f.write(path)

try:
  os.makedirs(args.output_dir)
except OSError as exception:
  if exception.errno != errno.EEXIST:
    raise
  else:
    logging.warn("Output FST directory already exists.")

with open(args.src) as reader:
  sen_counts = [l.split().count(str(args.glue_id))+1 for l in reader]

c = fst.Compiler()
cur_sen_idx = 0
cur_doc_idx = 0
fst_arc(c, 0, 1, args.bos_id)
cur_sen_start_node = 1
cur_sen_end_node = 2
next_free_node = 3
with open(args.nbest) as reader:
  for line in reader:
    parts = line.strip().split("|")
    sen_idx = int(parts[0].strip())
    sen = map(int, parts[3].strip().split())
    sen_cost = -float(parts[-1].strip())
    if sen_idx != cur_sen_idx:
      sen_counts[cur_doc_idx] -= 1
      if sen_counts[cur_doc_idx] > 0:
        fst_arc(c, cur_sen_end_node, next_free_node, args.glue_id)
        cur_sen_start_node = next_free_node
        cur_sen_end_node = next_free_node + 1
        next_free_node += 2
      else: # New document
        fst_finalize(c, cur_sen_end_node, next_free_node, "%s/%d.fst" % (args.output_dir, cur_doc_idx+1))
        c = fst.Compiler()
        cur_doc_idx += 1
        fst_arc(c, 0, 1, args.bos_id)
        cur_sen_start_node = 1
        cur_sen_end_node = 2
        next_free_node = 3
      cur_sen_idx = sen_idx
    # Add path from cur_sen_start_node to cur_sen_end_node
    if sen:
      prev_node = cur_sen_start_node
      for token in sen[:-1]:
        fst_arc(c, prev_node, next_free_node, token)
        prev_node = next_free_node
        next_free_node += 1
      fst_arc(c, prev_node, cur_sen_end_node, sen[-1], sen_cost)

fst_finalize(c, cur_sen_end_node, next_free_node, "%s/%d.fst" % (args.output_dir, cur_doc_idx+1))

