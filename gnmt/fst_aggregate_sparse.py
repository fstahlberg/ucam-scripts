'''
This script can be used to aggeregate the scores from ensembled
NMT into a single sparse tuple dimension
'''

import logging
import argparse
import sys

parser = argparse.ArgumentParser(description='Reads an FST from stdin with sparse tuple weights '
                                 'in text format and aggregates the scores from a number of dimensions '
                                 'into a single dimension. ATTENTION: openfst 1.5 text format is used, not 1.3!')
parser.add_argument('-r','--range', help='Range of dimensions to combine to target', required=True)
parser.add_argument('-t','--target', help='Target dimension', required=True)
args = parser.parse_args()

target = int(args.target)
tmp1,tmp2 = args.range.split(':')
r1 = int(tmp1)
r2 = int(tmp2)

for line in sys.stdin:
    parts = line.strip().split()
    if len(parts) != 5:
        print(line.strip())
    else:
        els = parts[4].split(",")
        scores = {int(els[idx]): float(els[idx+1]) for idx in xrange(1, len(els), 2)}
        agg_scores = {}
        for d in scores:
            if d >= r1 and d <= r2:
                agg_scores[target] = agg_scores.get(target, 0.0) + scores[d]
            else:
                agg_scores[d] = scores[d]
        parts[4] = "0," + (",".join([("%d,%f" % (d,agg_scores[d])) for d in sorted(agg_scores)]))
        print("\t".join(parts))
