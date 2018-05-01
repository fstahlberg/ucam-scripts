'''
Reads matrices in CSV format and applies transformation operations on them
'''
import argparse
import operator
import sys
import numpy as np
import os.path

parser = argparse.ArgumentParser(description='Converts an alignment matrix to Pharaoh format.')
parser.add_argument('-r','--range', help='For using %d placeholders in the other arguments')
parser.add_argument('-s','--source', help='Source  alignment matrix', default='-')
args = parser.parse_args()

f,t = args.range.split(":") if args.range else ('1','1')

def get_path(path, idx):
    if '%d' in path:
        return path % idx
    return path

def load(path, idx):
    if path == '-':
        m = np.loadtxt(sys.stdin)
    else:
        p = get_path(path, idx)
        if not os.path.isfile(p):
            return None
        m = np.loadtxt(p)
    if m.ndim < 2:
        m = np.array([m], ndmin=2)
    return m 

for idx in xrange(int(f), int(t)+1):
    m = load(args.source, idx)
    entries = []
    for row in xrange(m.shape[0]):
        for col in xrange(m.shape[1]):
            entries.append("%d-%d:%f" % (row,
                                         col,
                                         m[row,col]))
    print(' '.join(entries))

