'''
This script applies a word map to sentences in stdin. If --dir is
s2i, the word strings in stdin are converted to their ids. If
--dir is i2s, we convert word IDs to their readable representations.

ATTENTION: USES OLD INDEXING (TensorFlow style)
'''

import logging
import argparse
import sys

def load_wmap(path):
    with open(path) as f:
        d = dict(line.strip().split(None, 1) for line in f)
        for (s, i) in [('_PAD', '0'), ('_GO', '1'), ('_EOS', '2'), ('_UNK', '3')]:
            if d[s] != i:
                logging.warning("%s has not ID %s in word map %s!" % (s, i, path))
        return d

parser = argparse.ArgumentParser(description='Convert between written and ID representation of words. '
                                 'ATTENTION: Uses old (TensorFlow stylye) indexing'
                                 'Usage: python apply_wmap.py < in_sens > out_sens')
parser.add_argument('-d','--dir', help='s2i: convert to IDs (default), i2s: convert from IDs',
                    required=False)
parser.add_argument('-m','--wmap', help='Word map to apply (format: word id)',
                    required=True)
args = parser.parse_args()

wmap = load_wmap(args.wmap)
unk = wmap["_UNK"] if ("_UNK" in wmap) else '0'
if args.dir and args.dir == 'i2s': # inverse wmap
    wmap = dict(zip(wmap.values(), wmap.keys()))
    unk = "_NOTINWMAP"

for line in sys.stdin:
    print(' '.join([wmap[w] if (w in wmap) else unk for w in line.strip().split()]))
