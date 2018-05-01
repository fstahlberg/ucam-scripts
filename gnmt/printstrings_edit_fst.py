'''
This script is the printstrings equivalent for lattices composed
with an edit distance transducer (see create_edit_fst_directory.sh)

It searches for the n best paths, and outputs the input labels along it.
If the input label is UNK, output the output labels instead.
'''

import logging
import argparse
import sys
import os
import fst  # pyfst
from subprocess import call
from shutil import copyfile

def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")

parser = argparse.ArgumentParser(description='This script prints the n best paths in a lattice which has '
                                 'been created with create_edit_fst_directory.sh. It prints the input '
                                 'labels along the paths. If the input label is UNK, print the output labels '
                                 'instead. This case corresponds to HiFST fixing the UNKs in NMT.'
                                 'Usage: python printstrings_edit_fst.py --range 1:10 --input "editlats/?.fst.gz"')
parser.register('type','bool',str2bool)
parser.add_argument('-i','--input', help='Path to the input lattices.',
                    required=True)
parser.add_argument('-r','--range', help='Format: <from-idx>:<to-idx> (both inclusive). If --input contains an ? '
                    'replace it with indices specified by --range')
parser.add_argument('-n', "--nbest", default=0, type=int, required=False,
                    help="Set to a positive values to print n-best lists in Moses format. Note: sentence IDs start with "
                    "0, so IDs in the n-best list will be shifted by one")
parser.add_argument('-k', "--unk_id", default=999999998, type=int, required=False,
                    help="Reserved label for UNK. See create_edit_fst_directory.sh")
parser.add_argument('-u', '--unique', default=True, type='bool',
                    help="Remove duplicates in the n-best list. This might lead to less entries than n.")
parser.add_argument('-f', '--format', default='plain', help="Output format. Available: 'moses', 'plain', 'plain+weight'. "
                    "plain and plain+weight correspond to the format of HiFSTs printstrings. 'moses' multiplies the "
                    "scores by -1 to make it consistent with the SGNMT output")
parser.add_argument('-p','--print_unk', help='Do not replace UNK with output label', action='store_true')

args = parser.parse_args()

TMP_FILENAME = '/tmp/printstrings.%s.fst' % os.getpid()
logging.getLogger().setLevel(logging.INFO)
UNK_ID = args.unk_id
EPS_ID = 0

def load_fst(path):
    try:
        if path[-3:].lower() == ".gz":
            copyfile(path, "%s.gz" % TMP_FILENAME)
            call(["gunzip", "%s.gz" % TMP_FILENAME])
            ret = fst._fst.read(TMP_FILENAME)
            os.remove(TMP_FILENAME)
        else: # Fst not zipped
            ret = fst._fst.read(path)
        logging.debug("Read fst from %s" % path)
        return ret
    except:
        logging.error("Error reading fst from %s: %s" %
            (path, sys.exc_info()[1]))
    try:
        os.remove(TMP_FILENAME)
    except OSError:
        pass
    return None

def dfs(cur_fst, root_node, stub = [], acc_weight = 0.0):
    hypos = []
    if cur_fst[root_node].final:
        hypos.append((acc_weight, [w for w in stub if w != EPS_ID]))
    for arc in cur_fst[root_node].arcs:
        w = arc.olabel if arc.ilabel == UNK_ID and not args.print_unk else arc.ilabel
        hypos.extend(dfs(cur_fst, arc.nextstate, stub + [w], acc_weight + float(arc.weight)))
    return hypos


''' Very simple Trie implementation '''
class SimpleNode:
    def __init__(self):
        self.edges = {} # outgoing edges with terminal symbols
        self.element = None # rules at this node
        
class SimpleTrie:
    ''' This Trie implementation is simpler than the one in cam.gnmt.predictors.grammar
    because it does not support non-terminals or removal. However, for the cache in the
    greedy heuristic its enough. '''
    
    def __init__(self):
        self.root = SimpleNode()
    
    def _get_node(self, seq):
        cur_node = self.root
        for token_id in seq:
            children = cur_node.edges
            if not token_id in children:
                children[token_id] = SimpleNode()
            cur_node = children[token_id]
        return cur_node
    
    def add(self, seq, element):
        self._get_node(seq).element = element
        
    def get(self, seq):
        return self._get_node(seq).element

ids = [1]
if args.range:
    f,t = args.range.split(":")
    ids = range(int(f), int(t)+1)
nbest = args.nbest if args.nbest > 0 else 1

for fst_id in ids:
    cur_fst = load_fst(args.input.replace('?', str(fst_id)))
    if cur_fst:
        paths = cur_fst.shortest_path(nbest)
        hypos = dfs(paths, paths.start)
        hypos.sort(key=lambda hypo: hypo[0])
        if args.unique:
            trie = SimpleTrie()
            filtered_hypos = []
            for hypo in hypos:
                if trie.get(hypo[1]):
                    continue
                trie.add(hypo[1], hypo)
                filtered_hypos.append(hypo)
            hypos = filtered_hypos
        if not hypos:
            logging.fatal("Not hypothesis for %d!" % fst_id)
        for hypo in hypos:
            sen = ' '.join([str(w) for w in hypo[1]])
            score = hypo[0]
            if args.format == 'plain':
                print(sen)
            elif args.format == 'plain+weight':
                print("%s\t%f" % (sen, score))
            elif args.format == 'moses':
                print("%d ||| %s ||| %f" % (fst_id-1, sen, -score))
