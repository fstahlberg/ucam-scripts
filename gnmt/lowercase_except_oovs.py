'''
Use this script if source side is trained lower-cased to create correctly
cased OOV pass through rules
'''

import logging
import argparse
import sys

def load_wmap(path, inverse=False):
    with open(path) as f:
        d = dict(line.strip().split(None, 1) for line in f)
        if inverse:
            d = dict(zip(d.values(), d.keys()))
        return d

parser = argparse.ArgumentParser(description='Transform words at stdin to lowercase, but only if they are in the'
                                 ' given vocabulary. Otherwise, do not change casing. '
                                 'This is useful if the source side is trained lower-cased but you want to preserve '
                                 'OOV casing for the pass-through rules in HiFST '
                                 'Usage: python lowercase_except_oovs.py -m wmap.en < in_sens > out_sens')
parser.add_argument('-m','--wmap', help='Word map which defines the vocabulary (format: see -i parameter)',
                    required=True)
parser.add_argument('-i','--inverse_wmap', help='Use this argument to use word maps with format "id word".'
                    ' Otherwise the format "word id" is assumed', action='store_true')
args = parser.parse_args()

wmap = load_wmap(args.wmap, args.inverse_wmap)

for line in sys.stdin:
    print(' '.join([w.lower() if w.lower() in wmap else w for w in line.strip().split()]))
