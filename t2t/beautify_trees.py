# coding=utf-8
r"""Converts one-tree-per-line format to a more readable form."""

import logging
import argparse
import sys
import ptb_helper

parser = argparse.ArgumentParser(description='Converts syntax trees to a more readable form')
parser.add_argument('-w','--width', help='Number of indention blanks.', default=2)
args = parser.parse_args()
logging.getLogger().setLevel(logging.INFO)

#whitespace = "|%s" % (" " * (args.width - 1))
for idx, line in enumerate(sys.stdin):
  sys.stdout.write("\n# ID %d\n" % idx)
  tokens = line.replace(")", " ) ").strip().split()
  depth = 0
  for token in tokens:
    if token.startswith("("):
      indention = "%d%s" % (depth, " " * (2 - len(str(depth)) + args.width * depth))
      sys.stdout.write("\n%s%s" % (indention, token))
      depth += 1
    elif token == ")":
      depth -= 1
      sys.stdout.write("%s" % token)
    else:
      sys.stdout.write(" %s" % token)
  sys.stdout.write("\n")      

