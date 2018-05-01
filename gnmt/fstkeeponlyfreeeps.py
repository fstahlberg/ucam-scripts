"""This script reads a lattice and turns it into an n-gram acceptor
which accepts all strings if they consists only of n-grams in the
lattice. We incorporate n-grams up to a certain lengths, and connect
connect states with the same n-gram history with epsilon arcs with
a sparse tuple weight in the n-th weight component. The first
weight component holds the original lattice weights.
"""

import logging
import argparse
import sys
import pywrapfst as fst
import os.path

parser = argparse.ArgumentParser(description='Builds an FST with sparse tuple arcs which accepts strings if '
                                 'they consists only of n-grams in the lattice.')
parser.add_argument('-i','--input', help='Input lattice(s)', required=True)
parser.add_argument('-o','--output', help='Output lattice(s) (will be written)', required=True)
parser.add_argument('-n', "--ngram", default=3, type=int, required=False, help="Maximum n-gram length")
args = parser.parse_args()
max_hist_len = args.ngram

def get_path(pattern, idx):
    if '%d' in pattern:
        return pattern % idx
    return pattern if idx == 1 else False

def w2f(fstweight):
    """Converts an arc weight to float """
    return float(str(fstweight))

def out_state(state):
    return 10000000+state

def dfs(root, hist):
    global max_hist_len, visited, hist2node, lat, c
    if root in visited:
        return
    out_root = out_state(root)
    visited[root] = True
    if abs(w2f(lat.final(root))) < 0.001:
        c.write("%d\n" % out_root)
    for hist_len in xrange(1, min(len(hist)+1, max_hist_len)):
        key = ' '.join(hist[-hist_len:])
        if not key in hist2node: 
            hist2node[key] = [root]
        else:
            hist2node[key].append(root)
    c.write("%d\t%d\t0\t0\n" % (root, out_root))
    for arc in lat.arcs(root):
        c.write("%d\t%d\t%d\t%d\t0,1,%f\n" % (
            out_root,
            arc.nextstate,
            arc.ilabel,
            arc.olabel,
            w2f(arc.weight)))
        dfs(arc.nextstate, hist + [str(arc.ilabel)])

idx = 0
while True:
    idx += 1
    input_path = get_path(args.input, idx)
    if not input_path or not os.path.isfile(input_path):
        break
    lat = fst.Fst.read(input_path)
    # Collect info about states
    has_free_eps = {}
    
    for state in f.states():
    c = fst.Compiler(arc_type="tropicalsparsetuple")
    hist2node = {}
    visited = {}
    dfs(lat.start(), [])
    # Add context states
    next_context_id = 20000000
    for key,cluster in hist2node.iteritems():
        hist_len = len(key.split())
        if len(cluster) < 2:
            continue # We don't need this context
        elif len(cluster) == 2: # Directly connect both nodes
            c.write("%d\t%d\t%d\t%d\t0,%d,1.0\n" % (
                cluster[0], out_state(cluster[1]), 0, 0, hist_len+1))
            c.write("%d\t%d\t%d\t%d\t0,%d,1.0\n" % (
                cluster[1], out_state(cluster[0]), 0, 0, hist_len+1))
        else: # Introduce a context node
            next_context_id += 1
            for node in cluster:    
                c.write("%d\t%d\t%d\t%d\t0,%d,1.0\n" % (
                    node, next_context_id, 0, 0, hist_len+1))
                c.write("%d\t%d\t%d\t%d\n" % (
                    next_context_id, out_state(node), 0, 0))
    out_lat = c.compile()
    out_lat.arcsort()
    out_lat.write(get_path(args.output, idx))

