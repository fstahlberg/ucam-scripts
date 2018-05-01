"""This script replaces a corpus with positional UNK tokens: Each word
index larger than vocabulary size is replaced by the index
vocab_size + n, where n is the number of UNKs seen so far
"""

import logging
import argparse
import sys

parser = argparse.ArgumentParser(description='Replaces all word indices larger than vocab size (UNKs) '
                                 'with the index vocab size + n, where n is the number of previous UNKs '
                                 'in the same line.')
parser.add_argument('-v','--vocab_size', help='Vocabulary size', required=True)
args = parser.parse_args()

vocab_size = int(args.vocab_size)
for line in sys.stdin:
    words = []
    n = 0
    for w in line.strip().split():
        if int(w) < vocab_size and w != '0':
            words.append(w)
        else:
            words.append(str(vocab_size + n))
            n += 1
    print(' '.join(words))
