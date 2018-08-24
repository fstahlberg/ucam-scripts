# coding=utf-8
r"""This script creates FSTs for incorporating phrase tables or constraints
into OSNMT.
"""

import logging
import argparse
import sys
import os
import pywrapfst as fst
import errno

BOS_ID = 2
EOS_ID = 1
EOP_ID = 4
GAP_ID = 5
JUMP_FWD_ID = 6
JUMP_BWD_ID = 7

parser = argparse.ArgumentParser(description='Creates FSTs for incorporating phrases into osnmt')
parser.add_argument('-v','--vocab_size', help='Vocabulary size',
                    type=int, required=True)
parser.add_argument('-o','--output_dir', help='Output directory.',
                    required=True)
parser.add_argument('-s','--start_id', help='ID of the first FST',
                    type=int, default=1)
args = parser.parse_args()
logging.getLogger().setLevel(logging.INFO)

try:
  os.makedirs(args.output_dir)
except OSError as exception:
  if exception.errno != errno.EEXIST:
    raise
  else:
    logging.warn("Output FST directory already exists.")


def fst_arc(c, from_id, to_id, label):
  c.write("%d\t%d\t%d\t%d\n" % (from_id, to_id, label, label))


def fst_star_self_loop(c, state_id, vocab_size):
  fst_arc(c, state_id, state_id, 999)

  
fst_id = args.start_id
for line in sys.stdin:
  src_sentence = [int(i) for i in line.strip().split()]
  src_len = len(src_sentence)
  c = fst.Compiler()
  # Create base
  fst_arc(c, 0, 1, BOS_ID)
  for state_id in xrange(1, src_len + 1):
    fst_star_self_loop(c, state_id, args.vocab_size)
    fst_arc(c, state_id, state_id + 1, EOP_ID)
  fst_arc(c, src_len + 1, src_len + 2, EOS_ID)
  c.write("%d\n" % (src_len + 2,))
  f = c.compile()
  f.write("%s/%d.fst" % (args.output_dir, fst_id))
  fst_id += 1
