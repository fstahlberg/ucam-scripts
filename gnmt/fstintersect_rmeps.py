"""This script intersects two fsts and retains only the best path
for each input sequence (unique up to epsilon arcs).
It works best if the first fst (small) is small without many epsilons
and the second fst (large) is large with many epsilons.
"""

import logging
import argparse
import sys
import pywrapfst as fst
import os.path

parser = argparse.ArgumentParser(description='Keeps the best paths for each input sequence of '
                                 'the intersection of two FSTs.')
parser.add_argument('-i1','--input1', help='First input lattice(s) (small, without many eps)', required=True)
parser.add_argument('-i2','--input2', help='Second input lattice(s) (large, with many eps)', required=True)
parser.add_argument('-o','--output', help='Output lattice(s) (will be written)', required=True)
parser.add_argument('-n', "--ngram", default=3, type=int, required=False, help="n-gram length")
args = parser.parse_args()
hist_len = args.ngram - 1

def get_path(pattern, idx):
    if '%d' in pattern:
        return pattern % idx
    return pattern if idx == 1 else False

def search(root, lat2_paths):
    # root is a node in lat which defines the current history
    # lat2_paths are weights which could be added to the current
    # path in lat1 if the key does not get discarded in the 
    # future
    global lat, lat2, visited
    eps_paths = {node : [] for node in lat2_paths}
    open_paths = dict(eps_paths)
    while open_paths:
        next_open = {}
        for node,path in open_paths.iteritems():
            if node in eps_paths:
                continue
            for arc in lat2.arcs(node):
                if arc.olabel == 0:
                    if node in next_open:
                        
                    
      
    
    # Add paths to eps reachable nodes
    while open_nodes:
    visited = 
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
    input_path1 = get_path(args.input1, idx)
    if not input_path or not os.path.isfile(input_path1):
        break
    input_path2 = get_path(args.input2, idx)
    lat = fst.Fst.read(input_path1)
    lat.rmepsilon()
    lat.determinize()
    lat.minimize()
    lat2 = fst.Fst.read(input_path2)
    visited = {}
    search(lat.start(), [lat2.start()])
    lat.write(get_path(args.output, idx))

