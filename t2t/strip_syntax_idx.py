# coding=utf-8
r"""Strips IDs larger than a threshold from stdin."""

import logging
import argparse
import sys
import ptb_helper

parser = argparse.ArgumentParser(description='Remove IDs greater than --max_id from stdin.')
parser.add_argument('-m','--max_id', help='Maximum allowed ID.', type=int, required=True)
args = parser.parse_args()

for line in sys.stdin:
  print(" ".join([el for el in line.strip().split() if int(el) <= args.max_id]))

