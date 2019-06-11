# coding=utf-8
r"""Prints hypo in the lattice with smallest edit distance to
the reference.
"""

import logging
import argparse
import sys
import os
import pywrapfst as fst
import errno

parser = argparse.ArgumentParser(description='Get hypo in lattice with smallest Levenshtein distance to reference.')
parser.add_argument('-b','--bos_id', help='BOS ID.', required=False, type=int, default=2)
parser.add_argument('-e','--eos_id', help='EOS ID.', required=False, type=int, default=1)
parser.add_argument('-f','--fst_dir', help='Output directory.', required=True)
args = parser.parse_args()
logging.getLogger().setLevel(logging.INFO)


def fst_arc(c, ilabel, olabel, weight=0.0):
  c.write("0\t0\t%d\t%d\t%f\n" % (ilabel, olabel, weight))

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

for sen_idx, line in enumerate(sys.stdin):
  ref = [args.bos_id] + map(int, line.strip().split()) + [args.eos_id]
  ref_vocab = set(ref)
  hypo_vocab = set()
  #hypo_fst = fst.Fst.read("%s/%d.fst" % (args.fst_dir, sen_idx+1))
  hypo_fst = fst.Fst.read("%s/%04d.fst" % (args.fst_dir, sen_idx+1))
  hypo_fst.arcsort()
  hypo_fst = fst.arcmap(hypo_fst, map_type="rmweight")
  for state in hypo_fst.states():
    for arc in hypo_fst.arcs(state):
      if arc.ilabel != 0:
        hypo_vocab.add(arc.ilabel)
  # Build Levenshtein transducer
  c = fst.Compiler()
  c.write("0\n")
  for ref_label in ref_vocab:
    for hypo_label in hypo_vocab:
      if ref_label != hypo_label:
        fst_arc(c, ref_label, hypo_label, weight=1.0)  # sub
    fst_arc(c, ref_label, ref_label, weight=0.0)  # id
    fst_arc(c, ref_label, 0, weight=1.0)  # del
  for hypo_label in hypo_vocab:
    fst_arc(c, 0, hypo_label, weight=1.0)  # ins
  lev_fst = c.compile()
  lev_fst.arcsort()
  # Build reference transducer
  c = fst.Compiler()
  for idx, label in enumerate(ref):
    c.write("%d\t%d\t%d\t%d\n" % (idx, idx+1, label, label))
  c.write("%d\n" % len(ref))
  ref_fst = c.compile()
  reflev_fst = fst.compose(ref_fst, lev_fst)
  reflev_fst.arcsort()
  search_fst = fst.compose(reflev_fst, hypo_fst)
  oracle_fst = fst.shortestpath(search_fst)
  oracle_fst.topsort()
  oracle_str = []
  cur_state = 0
  while oracle_str[-1:] != [args.eos_id]:
    for arc in oracle_fst.arcs(cur_state):
      if arc.olabel != 0:
        oracle_str.append(arc.olabel)
      break
    cur_state = arc.nextstate
  print(" ".join(map(str, oracle_str[1:-1])))

