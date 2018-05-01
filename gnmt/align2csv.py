'''
This script converts a line from an alignment file to a
csv file
'''
import argparse
import operator
import sys

parser = argparse.ArgumentParser(description='Converts a single line of a alignment '
                            'text file to csv format.')
args = parser.parse_args()

weights = {}
max_src = 0
max_trg = 0
for pair in ' '.join(sys.stdin.readlines()).split():
    if ":" in pair:
        tmp,weight = pair.split(":")
    else:
        tmp = pair
        weight = "1.0"
    s,t = tmp.split("-")
    src_pos = int(s)
    trg_pos = int(t)
    max_src = max(max_src, src_pos)
    max_trg = max(max_trg, trg_pos)
    if not src_pos in weights:
        weights[src_pos] = {}
    weights[src_pos][trg_pos] = weight

for src_pos in range(max_src+1):
    line = weights.get(src_pos, {})
    print(' '.join([line.get(trg_pos, "0.0") for trg_pos in xrange(max_trg+1)]))
