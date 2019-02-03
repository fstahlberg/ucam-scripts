'''
Replaces words in an arpa LM with their indices
'''

import logging
import argparse
import sys

def load_wmap(path, inverse=False):
    with open(path) as f:
        d = dict(line.strip().split(None, 1) for line in f)
        if inverse:
            d = dict(zip(d.values(), d.keys()))
        for (s, i) in [('</s>', '1'), ('<s>', '2'), ('<unk>', '3')]:
            if not s in d or d[s] != i:
                logging.warning("%s has not ID %s in word map %s!" % (s, i, path))
        return d

parser = argparse.ArgumentParser(description='Replaces words in arpa LM with their IDs. '
                                 'Usage: python idx_lm.py -m wmap < word-lm > idx-lm')
parser.add_argument('-m','--wmap', help='Word map to apply (format: see -i parameter)',
                    required=True)
parser.add_argument('-i','--inverse_wmap', help='Use this argument to use word maps with format "id word".'
                    ' Otherwise the format "word id" is assumed', action='store_true')
args = parser.parse_args()

wmap = load_wmap(args.wmap, args.inverse_wmap)
#unk = '0'
#unk = '999999998'
unk = '3'
wmap['<s>'] = '<s>'
wmap['</s>'] = '</s>'
wmap['<unk>'] = '<unk>'

for line in sys.stdin:
    parts = line.strip().split("\t")
    if len(parts) < 2:
        print(line.strip())
    else:
        parts[1] = ' '.join([wmap.get(w, unk) for w in parts[1].split()])
        print("\t".join(parts))
