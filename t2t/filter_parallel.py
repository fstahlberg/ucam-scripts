r"""Expected format
123 234 345|12 3221 22
"""

import argparse
import sys

parser = argparse.ArgumentParser(description='Filters parallel indexed text')
parser.add_argument('-r','--ratio', help='Max ratio.', default=4.5)
parser.add_argument('-u','--unk', help='UNK.', default='3')
parser.add_argument('-m','--max_length', help='Max length', default=240)
args = parser.parse_args()

for line in sys.stdin:
  src, trg = line.split("|")
  src_words = src.strip().split()
  trg_words = trg.strip().split()
  src_count = len(src_words)
  trg_count = len(trg_words)
  if (min(src_count, trg_count) > 0 
      and max(src_count, trg_count) < args.max_length 
      and max(float(src_count) / float(trg_count), 
              float(trg_count) / float(src_count)) < args.ratio 
      and not args.unk in src_words 
      and not args.unk in trg_words):
    sys.stdout.write(line)

