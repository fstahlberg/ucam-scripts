'''
This script reads a nbest file in Moses format with sparse features
and outputs a training file for libsvm-svmrank.
'''

import logging
import argparse
import sys

parser = argparse.ArgumentParser(description='Reads a nbest file in Moses format and converts it to a training file '
                                 'for libsvm.')
parser.add_argument('-x','--exclude_features', help='Comma separated list of features (0-indexed) not to include.', default='', type=str)
parser.add_argument('-l','--len_div', help='Use sentence_length/len_div as feature.', default=50.0, type=float)
args = parser.parse_args()

exclude_features = []
if args.exclude_features:
  exclude_features = map(int, args.exclude_features.split(","))

for line in sys.stdin:
    parts = line.split('|')
    feats = parts[6].strip().split()
    l = float(len(parts[3].strip().split()))
    out_feats = [l* l / args.len_div]
    for i in xrange(1, len(feats),2):
      if i // 2 not in exclude_features:
        out_feats.append(float(feats[i]))
    print("%s qid:%s %s" % (parts[9].strip(),
                            parts[0].strip(),
                            " ".join(["%d:%f" % (i+1, f/l) for i, f in enumerate(out_feats)])))

