# coding=utf-8
r"""Extracts fertilities from (integer) OSM sequences"""

import logging
import argparse
import sys

parser = argparse.ArgumentParser(description='Extracts fertilities from integer OSM sequences.')
parser.add_argument('-o','--offset', default=4, type=int, help='ID of fertility 0.')
parser.add_argument('-v','--vocab_size', default=20, type=int, help='Limits fertility (everything else is <unk>=3).')
parser.add_argument('-p','--eop_symb', default='4', help='EOP symbol.')
parser.add_argument('-u','--unk_symb', default='3', help='UNK symbol.')
parser.add_argument('-e','--exclude_list', default='6,7', help='Symbols not contributing to the fertility value.')
args = parser.parse_args()

excluded = args.exclude_list.split(',')


for line in sys.stdin:
  ferts = []
  fert = args.offset
  for word in line.strip().split():
    if word == args.eop_symb:
      ferts.append(fert)
      fert = args.offset
    elif word not in excluded:
      fert += 1
  ferts.append(fert+1) # +1 for producing EOS
  print(' '.join([str(f) if f < args.vocab_size else args.unk_symb for f in ferts]))
