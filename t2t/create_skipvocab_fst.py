# coding=utf-8
r"""Creates an FST in text format which deletes all IDs above a threshold.
"""

import argparse

parser = argparse.ArgumentParser(description='Creates an FST in text format which deletes all IDs above a threshold.')
parser.add_argument('-m','--max_terminal_id', help='All IDs less or equal this are identity mapped.',
                    required=True, type=int)
parser.add_argument('-v','--vocab_size', help='Vocabulary size.', required=True, type=int)
args = parser.parse_args()

for i in xrange(1, args.max_terminal_id + 1):
  print("0 0 %d %d" % (i, i))

for i in xrange(args.max_terminal_id + 1, args.vocab_size):
  print("0 0 %d 0" % i)

print("0")

