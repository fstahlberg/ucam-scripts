'''
Reads matrices in CSV format and applies transformation operations on them
'''
import argparse
import operator
import sys
import numpy as np
import os.path

parser = argparse.ArgumentParser(description='Applies matrix operations on CSV files.')
parser.add_argument('-r','--range', help='For using %d placeholders in the other arguments')
parser.add_argument('-s1','--source1', help='First source matrix', default='-')
parser.add_argument('-s2','--source2', help='Second source matrix if required', default='')
parser.add_argument('-t','--target', help='Target matrix to write', default='-')
parser.add_argument('-o','--operations', help='Comma-separated list of operations: '
                    'sum,transpose,norm')
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
    m1 = load(args.source1, idx)
    m2 = load(args.source2, idx)
    for op_name in args.operations.split(','):
        if op_name == 'transpose':
            m1 = np.transpose(m1)
        elif op_name == 'sum':
            m1 = m1 + m2
        elif op_name == 'norm':
            m1 = m1/m1.sum(axis=1, keepdims=True)
    if args.target == '-':
        np.savetxt(sys.stdout, m1)
    else:
        np.savetxt(get_path(args.target, idx), m1)
