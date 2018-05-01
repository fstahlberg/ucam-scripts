'''
This script converts sparse tuple FSTs to standard arcs
'''

import logging
import argparse
import sys

parser = argparse.ArgumentParser(description='Reads an FST from stdin with sparse tuple weights '
                                 'in text format and converts it to standard arcs by applying a '
                                 'weight vector. ATTENTION: openfst 1.5 text format is used, not 1.3!')
parser.add_argument('-w','--weights', help='Comma separated weights without gamma (see GNMT\'s --predictor_weights).',
                    required=True)
args = parser.parse_args()

weights = [float(w) for w in args.weights.strip().split(",")]

for line in sys.stdin:
    parts = line.strip().split()
    if len(parts) != 5:
        print(line.strip())
    else:
        els = parts[4].split(",")
        score = sum([weights[int(els[idx])-1] * float(els[idx+1]) for idx in xrange(1, len(els), 2)])
        parts[4] = str(score)
        print("\t".join(parts))
