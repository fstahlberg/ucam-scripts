# coding=utf-8
r"""This script creates non-deterministic FSTs which can be used in SGNMT
for parsing constraints. The FSTs ensure that the full sentence is included in
the output. Additional, the output may be interspersed with syntactic
annotations:
- format layerbylayer_pop or layerbylayer: For upper layers, terminals must
  be in the right order, non-terminals may serve as placeholders for one or
  more terminals. After the last end-of-layer symbol, the exact terminal
  sequence must be produced (up to POPs)
- format flat_*: Terminal sequence may be interspersed with random syntactic
  annotations. Note that we do not check the balance of the syntactic tree as
  bracket languages are not regular.
"""

import logging
import argparse
import sys
import os
import pywrapfst as fst
import errno

parser = argparse.ArgumentParser(description='Create constraining FSTs for parsing. See docstring.'
                                 'Usage: create_parsing_fsts.py -l 123 -o lats -v vocab < in_sens ')
parser.add_argument('-l','--eol_id', help='For layerbylayer: ID of the end-of-layer symbol.',
                    required=False, type=int)
parser.add_argument('-b', '--bos_id', help='ID of the begin-of-sentence symbol. Default is T2T default.',
                    type=int, default=3,
                    required=False)
parser.add_argument('-e', '--eos_id', help='ID of the end-of-sentence symbol. Default is T2T default.',
                    type=int, default=1,
                    required=False)
parser.add_argument('-v','--vocab', help='T2T style vocabulary',
                    required=True)
parser.add_argument('-o','--output_dir', help='Output directory.',
                    required=True)
parser.add_argument('-f', '--format', default='layerbylayer_pop',
                    choices=['layerbylayer_pop', 'flat_starttagged', 'flat_endtagged', 'flat_bothtagged'],
                    help='Defines the structure of the generated FSTs. See docstring')
args = parser.parse_args()
logging.getLogger().setLevel(logging.INFO)

if args.format.startswith("layerbylayer") and args.eol_id is None:
  sys.exit("--eol_id must be set for layerbylayer* format")

non_terminals = []
pop_id = None
opening_non_terminals = []
closing_non_terminals = []
with open(args.vocab) as f:
  for idx, line in enumerate(f):
    line = line.strip()
    if line == "'##POP##'":
      pop_id = idx
      closing_non_terminals.append(idx)
    elif line[:3] == "'##" and line[-3:] == "##'":
      non_terminals.append(idx)
      if ")" in line:
        closing_non_terminals.append(idx)
      else:
        opening_non_terminals.append(idx)

if args.format == "layerbylayer_pop" and pop_id is None:
  sys.exit("##POP## not found in vocabulary")
logging.info("%d non-terminals found" % len(non_terminals))

try:
  os.makedirs(args.output_dir)
except OSError as exception:
  if exception.errno != errno.EEXIST:
    raise
  else:
    logging.warn("Output FST directory already exists.")


def fst_arc(c, from_id, to_id, label):
  c.write("%d\t%d\t%d\t%d\n" % (from_id, to_id, label, label))


def construct_layerbylayer_fst(c, non_terminals, terminals, pop_id=None):
  fst_arc(c, 0, 1, args.bos_id)
  state_id = 1
  line_offset = 10000 # Something larger than the longest sequence
  # Linear terminal connections plus POP
  for t in terminals:
    if pop_id is not None:
      fst_arc(c, state_id, state_id, pop_id)
      fst_arc(c, state_id + line_offset, state_id + line_offset, pop_id)
    fst_arc(c, state_id, state_id + 1, t)
    fst_arc(c, state_id + line_offset, state_id + line_offset + 1, t)
    state_id += 1
  if pop_id is not None:
    fst_arc(c, state_id, state_id, pop_id)
    fst_arc(c, state_id + line_offset, state_id + line_offset, pop_id)
  # EOS and EOL
  fst_arc(c, state_id, state_id + 1, args.eos_id)
  fst_arc(c, state_id + line_offset, 1, args.eol_id)
  # Nonterminal connections
  c.write("%d\n" % (state_id + 1,))
  for from_state_id in xrange(1, len(terminals) + 1):
    for to_state_id in xrange(from_state_id + 1, len(terminals) + 2):
      for nt in non_terminals:
        fst_arc(c, from_state_id, to_state_id + line_offset, nt)
        fst_arc(c, from_state_id + line_offset, to_state_id + line_offset, nt)


def construct_flat_fst(c, closing_non_terminals, opening_non_terminals, terminals):
  """Linear FST along terminals, with NT self loops."""
  fst_arc(c, 0, 1, args.bos_id)
  for nt in opening_non_terminals:
    fst_arc(c, 1, 1, nt)
  offset = 10000 # Something larger than the longest sequence
  offset2 = 2 * offset
  for idx, t in enumerate(terminals):
    state_id = idx + 2
    fst_arc(c, state_id - 1, state_id, t)
    fst_arc(c, state_id - 1 + offset2, state_id, t)
    for nt in closing_non_terminals:  # Self loop
      fst_arc(c, state_id, state_id + offset, nt)
      fst_arc(c, state_id + offset, state_id + offset, nt)
    if idx < len(terminals) - 1: # No opening at last position
      for nt in opening_non_terminals:
        fst_arc(c, state_id + offset, state_id + offset2, nt)
        fst_arc(c, state_id + offset2, state_id + offset2, nt)
  fst_arc(c, state_id, state_id + 1, args.eos_id)
  fst_arc(c, state_id + offset, state_id + 1, args.eos_id)
  c.write("%d\n" % (state_id + 1,))
  

for line_idx, line in enumerate(sys.stdin):
  terminals = [int(i) for i in line.strip().split()]
  c = fst.Compiler()
  # Debug with sys.stdout rather than c
  if args.format == 'layerbylayer':
    construct_layerbylayer_fst(c, non_terminals, terminals)
  elif args.format == 'layerbylayer_pop':
    construct_layerbylayer_fst(c, non_terminals, terminals, pop_id)
  else: # flat_*
    construct_flat_fst(c, closing_non_terminals, opening_non_terminals, terminals)
  f = c.compile()
  f.write("%s/%d.fst" % (args.output_dir, line_idx + 1))
