'''
This script calculates the OOV rates of the text on stdin
given a vocabulary.

TODO: This is quick and dirty rather than efficient
'''

import logging
import argparse
import sys

parser = argparse.ArgumentParser(description='Calculates the OOV rate on the text in stdin. '
                                 'Usage: python oov.py -v vocab-file < in_sens')
parser.add_argument('-v','--vocabulary', help='Vocabulary file',
                    required=True)
args = parser.parse_args()

voc = {}
with open(args.vocabulary) as f:
    for line in f:
        for word in line.strip().split():
            if word:
                voc[word] = True

unks = {}
text_voc = {}
n_unk = 0
n_words = 0
for line in sys.stdin:
    for word in line.strip().split():
        if not word: # empty lines
            continue
        n_words += 1
        text_voc[word] = True
        if not word in voc:
            unks[word] = True
            n_unk += 1

print("OOVs:")
for w in unks:
    print(w)
print("Vocabulary size: %d" % len(voc))
print("Number of words: %d" % n_words)
print("OOV (unique): %f" % (100.0 * len(unks) / len(text_voc))) 
print("OOV (running): %f" % (100.0 * n_unk / n_words))
