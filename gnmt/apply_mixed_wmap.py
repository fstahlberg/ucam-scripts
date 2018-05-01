"""This script applies a mixed word/character map to sentences in stdin. If --dir is
set to s2i, the word strings in stdin are converted to their ids. If
--dir is i2s, we convert word IDs to their readable representations.

See create_mixed_wmap.py for creating a mixed word/character wmap.
"""

import logging
import argparse
import sys

def load_wmap(path, inverse=False):
    with open(path) as f:
        d = dict(line.strip().split(None, 1) for line in f)
        if inverse:
            d = dict(zip(d.values(), d.keys()))
        for (s, i) in [('<s>', '1'), ('</s>', '2')]:
            if not s in d or d[s] != i:
                logging.warning("%s has not ID %s in word map %s!" % (s, i, path))
        return d

parser = argparse.ArgumentParser(description='Convert between written and ID representation of words. '
                                 'This script is designed for mixed word/character models as created by '
                                 'create_mixed_wmap.py. Entries starting with <b>, <m>, <e> are considered '
                                 'as character symbols to represent OOVs.'
                                 'Usage: python apply_mixed_wmap.py < in_sens > out_sens')
parser.add_argument('-d','--dir', help='s2i: convert to IDs (default), i2s: convert from IDs',
                    required=False)
parser.add_argument('-m','--wmap', help='Mixed Word/character map to apply (format: see -i parameter)',
                    required=True)
parser.add_argument('-i','--inverse_wmap', help='Use this argument to use word maps with format "id word".'
                    ' Otherwise the format "word id" is assumed', action='store_true')
args = parser.parse_args()

def collapse_chars(tokens):
    collapsed = []
    w = ''
    for t in tokens:
        if t[:3] == '<b>' and w:
            collapsed.append(w)
            w = ''
        if t[:3] == '<m>' or t[:3] == '<b>':
            w += t[3:]
        elif t[:3] == '<e>':
            collapsed.append(w + t[3:])
            w = ''
        else: # Normal word
            if w:
                collapsed.append(w)
                w = ''
            collapsed.append(t)
    if w:
        collapsed.append(w)
    return ' '.join(collapsed)

d = load_wmap(args.wmap, args.inverse_wmap)
if args.dir and args.dir == 'i2s': # integer to string
    wmap = dict(zip(d.values(), d.keys()))
    unk = "NOTINWMAP"
    # do not use for line in sys.stdin because incompatible with -u option
    # required for lattice mert
    while True:
        line = sys.stdin.readline()
        if not line: break # EOF
        print(collapse_chars([wmap.get(w, unk) for w in line.strip().split()]))
else: # string to integer
    wmap = {}
    bmap = {}
    mmap = {}
    emap = {}
    unk = '0'
    for w,i in d.items():
        if w[:3] == '<b>':
            bmap[w[3:]] = i
        elif w[:3] == '<m>':
            mmap[w[3:]] = i
        elif w[:3] == '<e>':
            emap[w[3:]] = i
        else:
            wmap[w] = i
    while True:
        line = sys.stdin.readline()
        if not line: break # EOF
        indices = []
        for w in line.strip().split():
            if w in wmap:
                indices.append(wmap[w])
            else: # OOV
                for pos,c in enumerate(w):
                    if pos == 0:
                        indices.append(bmap.get(c, unk))
                    elif pos == len(w) - 1:
                        indices.append(emap.get(c, unk))
                    else:
                        indices.append(mmap.get(c, unk))
        print(' '.join(indices))
