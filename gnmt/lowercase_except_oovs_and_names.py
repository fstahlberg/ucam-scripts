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
parser.add_argument('-f','--first_names', help='List of first names. If a last name occurs after a first name and its cased, do not change casing for any occurrence of this last name',
                    required=True)
parser.add_argument('-l','--last_names', help='List of last names.',
                    required=True)
parser.add_argument('-i','--inverse_wmap', help='Use this argument to use word maps with format "id word".'
                    ' Otherwise the format "word id" is assumed', action='store_true')
args = parser.parse_args()

wmap = load_wmap(args.wmap, args.inverse_wmap)

with open(args.first_names) as f:
    first_names = {line.strip().lower() : True for line in f}

with open(args.last_names) as f:
    last_names = {line.strip().lower() : True for line in f}

for line in sys.stdin:
    # Scan for names and delete it from wmap in case
    behind_first_name = False
    for w in line.strip().split():
        if behind_first_name and w.lower() in last_names and w.lower() in wmap and w.lower() != w:
            del wmap[w.lower()]
        behind_first_name = (w.lower() in first_names)
    # Print line
    print(' '.join([w.lower() if w.lower() in wmap else w for w in line.strip().split()]))
