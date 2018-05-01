'''
This script is a substitute for the old turn_oovs_into_ascii.pl
'''

import argparse
import sys
import operator

def load_wmap(path, inverse_wmap):
    with open(path) as f:
        if inverse_wmap:
            d = dict((word, int(word_id)) for (word_id, word) in (line.strip().split(None, 1) for line in f))
        else:
            d = dict((word, int(word_id)) for (word, word_id) in (line.strip().split(None, 1) for line in f))
        return d

parser = argparse.ArgumentParser(description='Substitute for turn_oovs_into_ascii.pl. For each OOV, output the line number and the word.')
parser.add_argument('-m','--wmap', help='Word map which defines the vocabulary (format: word id)',
                    required=True)
parser.add_argument('-i','--inverse_wmap', help='Use this argument to use word maps with format "id word".'
                    ' Otherwise the format "word id" is assumed', action='store_true')
args = parser.parse_args()

wmap = load_wmap(args.wmap, args.inverse_wmap)

line_id = 1
for line in sys.stdin:
    for w in line.strip().split():
        if w and (not w in wmap):
            print("%d %s" % (line_id, w))
    line_id = line_id + 1

