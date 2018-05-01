"""Creates a word map from the text at stdin
"""

import logging
import argparse
import sys
import operator

parser = argparse.ArgumentParser(description='Create a wmap from the text at stdin')
parser.add_argument('-r','--reserved_ids', help='Comma separated list of reserved IDs at the begin of the wmap.', 
                    default='<epsilon>,</s>,<s>,<unk>', required=False)
args = parser.parse_args()

words = {}

for line in sys.stdin:
    for word in line.strip().split():
        words[word] = words.get(word,0) + 1

reserved = args.reserved_ids.split(",")
for idx, symb in enumerate(reserved):
  print("%s %d" % (symb, idx))

offset = len(reserved)

for idx,word in enumerate([w for w,f in sorted(words.items(), key=operator.itemgetter(1), reverse=True)]):
    print("%s %d" % (word, idx+offset))
