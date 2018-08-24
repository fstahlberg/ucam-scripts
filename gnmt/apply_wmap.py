"""This script applies a word map to sentences in stdin. If --dir is
set to s2i, the word strings in stdin are converted to their ids. If
--dir is i2s, we convert word IDs to their readable representations.
"""

import logging
import argparse
import sys

def load_wmap(path, inverse=False):
    with open(path) as f:
        d = dict(line.strip().split(None, 1) for line in f)
        if inverse:
            d = dict(zip(d.values(), d.keys()))
        return d

def detok_id(line):
    return line

def detok_eow(line):
    return line.replace(" ", "").replace("</w>", " ").strip()

def detok_mixed(line):
    words = []
    part_word = ""
    for t in line.strip().split():
        if t[:3] == "<b>" or t[:3] == "<m>":
            part_word = part_word + t[3:]
        elif t[:3] == "<e>":
            words.append(part_word + t[3:])
            part_word = ""
        else:
            if part_word:
                words.append(part_word)
                part_word = ""
            words.append(t)
    if part_word:
        words.append(part_word)
    return ' '.join(words)

parser = argparse.ArgumentParser(description='Convert between written and ID representation of words. '
                                 'The index 0 is always used as UNK token, wmap entry for 0 is ignored. '
                                 'Usage: python apply_wmap.py < in_sens > out_sens')
parser.add_argument('-d','--dir', help='s2i: convert to IDs (default), i2s: convert from IDs',
                    required=False)
parser.add_argument('-m','--wmap', help='Word map to apply (format: see -i parameter)',
                    required=True)
parser.add_argument('-f','--fields', help='Comma separated list of fields (like for linux command cut)')
parser.add_argument('-u','--unk_id', default=3, help='UNK id')
parser.add_argument('-i','--inverse_wmap', help='Use this argument to use word maps with format "id word".'
                    ' Otherwise the format "word id" is assumed', action='store_true')
parser.add_argument('-t', '--tokenization', default='id', choices=['id', 'eow', 'mixed'],
                    help='This parameter adds support for tokenizations below word level. Choose '
                    '"id" if no further postprocessing should be applied after the mapping. "eow"'
                    'removes all blanks and replaces </w> tokens with new blanks. This can be used '
                    'for subword units with explicit end-of-word markers. "mixed" is the mixed '
                    'word/character model in Wu et al. (2016), in which the prefixes <b>, <m>, and '
                    '<e> annotate tokens on the character level. Use "eow" for pure character-level '
                    'tokenizations')

args = parser.parse_args()

wmap = load_wmap(args.wmap, args.inverse_wmap)
unk = str(args.unk_id)
if args.dir and args.dir == 'i2s': # inverse wmap
    wmap = dict(zip(wmap.values(), wmap.keys()))
    unk = "NOTINWMAP"

fields = None
if args.fields:
    fields = [int(f)-1 for f in args.fields.split(',')]

detok = detok_id
if args.tokenization == 'eow':
    detok = detok_eow
elif args.tokenization == 'mixed':
    detok = detok_mixed

# do not use for line in sys.stdin because incompatible with -u option
# required for lattice mert
while True:
    line = sys.stdin.readline()
    if not line: break # EOF
    if fields:
        words = line.strip().split()
        for f in fields:
            if f < len(words):
                words[f] = wmap.get(words[f], unk)
        print(detok("\t".join(words)))
    else:
        print(detok(' '.join([wmap[w] if (w in wmap) else unk for w in line.strip().split()])))
