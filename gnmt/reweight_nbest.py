'''
This script reads a nbest file in Moses format with sparse features
and reweights them.
'''

import logging
import argparse
import sys

parser = argparse.ArgumentParser(description='Reads a nbest file in Moses format and converts it to a reordered nbest '
                                 'list according the given weights. Note that all features need to be provided for each '
                                 'entry in the nbest list in the same order')
parser.add_argument('-w','--weights', help='Comma separated weight vector', required=True)
args = parser.parse_args()

weights = [float(w) for w in args.weights.split(',')]
n_feats = len(weights)

def print_cur_sens(cur_id, cur_sens):
    for (total, sen, feats_str) in sorted(cur_sens, key=lambda it: it[0], reverse=True):
        print("%d |||%s|||%s||| %f" % (cur_id, sen, feats_str, total))

cur_id = -1
cur_sens = []
for line in sys.stdin:
    parts = line.split('|')
    this_id = int(parts[0].strip())
    if cur_id != this_id:
        print_cur_sens(cur_id, cur_sens)
        cur_sens = []
        cur_id = this_id
    feats = parts[6].strip().split()
    feat_vals = []
    for feat in feats:
      try:
        val = float(feat)
        feat_vals.append(val)
      except:
        pass
    if len(feat_vals) != n_feats:
      sys.exit("Number of features does not match weight vector length")
    total = sum([weights[i]*feat_vals[i] for i in xrange(n_feats)])
    cur_sens.append((total, parts[3], parts[6]))
print_cur_sens(cur_id, cur_sens)
