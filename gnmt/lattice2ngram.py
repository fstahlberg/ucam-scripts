"""This script reads a lattice and turns it into an n-gram acceptor
which accepts all strings if they consists only of n-grams in the
lattice. This is realized by connecting all nodes with the same
n-gram history with epsilon arcs.
"""

import logging
import argparse
import sys
import pywrapfst as fst
import os.path

parser = argparse.ArgumentParser(description='Builds an FST which accepts strings if they consists only '
                                 'of n-grams in the lattice.')
parser.add_argument('-i','--input', help='Input lattice(s)', required=True)
parser.add_argument('-o','--output', help='Output lattice(s) (will be written)', required=True)
parser.add_argument('-n', "--ngram", default=3, type=int, required=False, help="n-gram length")
args = parser.parse_args()
hist_len = args.ngram - 1

def get_path(pattern, idx):
    if '%d' in pattern:
        return pattern % idx
    return pattern if idx == 1 else False

def dfs(root, hist):
    global hist_len, visited, hist2node, lat
    if root in visited:
        return
    visited[root] = True
    for arc in lat.arcs(root):
        dfs(arc.nextstate, hist + [str(arc.ilabel)])
    key = ' '.join(hist[-hist_len:])
    if key in hist2node: # connect with it
        arc1 = fst.Arc(0, 0, fst.Weight.One(lat.weight_type()), hist2node[key])
        arc2 = fst.Arc(0, 0, fst.Weight.One(lat.weight_type()), root)
        lat.add_arc(root, arc1)
        lat.add_arc(hist2node[key], arc2)
    else:
        hist2node[key] = root

idx = 0
while True:
    idx += 1
    input_path = get_path(args.input, idx)
    if not input_path or not os.path.isfile(input_path):
        break
    lat = fst.Fst.read(input_path)
    hist2node = {}
    visited = {}
    dfs(lat.start(), [])
    lat.write(get_path(args.output, idx))

