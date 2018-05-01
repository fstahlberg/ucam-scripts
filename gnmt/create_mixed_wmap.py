'''
This script creates a word map for a mixed character/word
model following Wu et al. (2016) (Google's NMT).
'''

import argparse
import sys
import operator

def load_wmap(path, inverse_wmap):
    with open(path) as f:
        if inverse_wmap:
            d = dict((el[-1], int(el[0])) for el in (line.strip().split() for line in f))
        else:
            d = dict((el[0], int(el[-1])) for el in (line.strip().split() for line in f))
        return d

parser = argparse.ArgumentParser(description='Outputs a wmap which contains all words in stdin '
                                 'with word IDs lower than n. Additionally, we add character symbols '
                                 'following Wu et al. (2016) to represent the words outside the vocabulary')
parser.add_argument('-m','--wmap', help='Word map to apply (format: word id)', required=True)
parser.add_argument('-t','--text', help='Additional text for collecting character counts')
parser.add_argument('-i','--inverse_wmap', help='Use this argument to use word maps with format "id word".'
                    ' Otherwise the format "word id" is assumed', action='store_true')
parser.add_argument('-n','--vocab_size', help='Largest word index. Words larger than this index are represented by character symbols',
                    required=True, type=int)
args = parser.parse_args()

wmap = load_wmap(args.wmap, args.inverse_wmap)
vocab_size = args.vocab_size

chars = {}
for w in wmap:
    for c in w:
        chars[c] = chars.get(c, 0) + 1
if args.text:
    with open(args.text) as f:
        for line in f:
            for w in line.strip().split():
                for c in w:
                    chars[c] = chars.get(c, 0) + 1
if ' ' in chars:
    del chars[' ']


# Print words
for w,i in sorted([el for el in wmap.items() if el[1] <= vocab_size], key=operator.itemgetter(1)):
    print("%s %d" % (w,i))

idx = vocab_size + 1
# Print chars
for c,n in sorted(chars.items(), key=operator.itemgetter(1), reverse=True):
    if n >= 5:
        print("<b>%s %d" % (c, idx))
        print("<m>%s %d" % (c, idx+1))
        print("<e>%s %d" % (c, idx+2))
        idx += 3
