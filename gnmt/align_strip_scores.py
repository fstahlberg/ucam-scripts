"""Removes the scores of in an alignment file
"""

import logging
import argparse
import sys

parser = argparse.ArgumentParser(description='Reads an alignment file from stdin and strips scores')
parser.add_argument('-t','--threshold', default=0.5, type=float, help='Minimum alignment score')
args = parser.parse_args()

eps = args.threshold
for line in sys.stdin:
    entries = []
    for entry in line.strip().split():
        if ':' in entry:
            pair,score = entry.split(':')
            if float(score) >= eps:
                entries.append(pair)
        else:
            entries.append(entry)
    print(' '.join(entries))
