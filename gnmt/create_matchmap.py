'''
This script extracts pairs of word indices, which map to the same
word (case insensitive). This can be used within
create_name_constraint_fst_directory.sh 
'''

import logging
import argparse
import sys

def load_wmap(path, inverse=False, lc = False): # lower case
    with open(path) as f:
        if lc:
            d = dict(line.lower().strip().split(None, 1) for line in f)
        else:
            d = dict(line.strip().split(None, 1) for line in f)
        if inverse:
            d = dict(zip(d.values(), d.keys()))
        for (s, i) in [('<s>', '1'), ('</s>', '2')]:
            if not s in d or d[s] != i:
                logging.warning("%s has not ID %s in word map %s!" % (s, i, path))
        return d

parser = argparse.ArgumentParser(description='Creates pairs of word indices which map to the same '
                                 'word (case insesitive). Usage: python create_matchmap.py -m1 bla -m2 bla2 > pairs')
parser.add_argument('-m1','--wmap1', help='First word map to apply (format: see -i parameter)',
                    required=True)
parser.add_argument('-m2','--wmap2', help='Second word map to apply (format: see -i parameter)',
                    required=True)
parser.add_argument('-v','--vocab', help='If provided, extract pairs only if word is in this wmap (format: see -i parameter)',
                    required=False)
parser.add_argument('-i','--inverse_wmap', help='Use this argument to use word maps with format "id word".'
                    ' Otherwise the format "word id" is assumed', action='store_true')
args = parser.parse_args()

wmap1 = load_wmap(args.wmap1, args.inverse_wmap)
wmap2 = load_wmap(args.wmap2, args.inverse_wmap)

words2 = {}
for w,idx in wmap2.iteritems():
    words2[w.lower()] = words2.get(w.lower(), []) + [idx]


vocab = None
if args.vocab:
    vocab = load_wmap(args.vocab, args.inverse_wmap, True)

for w,idx in wmap1.iteritems():
    lc_w = w.lower()
    if lc_w in words2 and (vocab is None or (lc_w in vocab)):
        print("%s is in vocab: %s" % (lc_w, vocab[lc_w]))
        for idx2 in words2[lc_w]:
            print("%s %s" % (idx, idx2))
