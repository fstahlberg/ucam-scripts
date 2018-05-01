'''
This script swaps indices in wmaps given a iterative rule.
'''

import logging
import argparse
import sys

import ast
import operator as op

# supported operators
# Math implementation from http://stackoverflow.com/questions/2371436/evaluating-a-mathematical-expression-in-a-string
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}

def eval_expr(expr):
    """
    >>> eval_expr('2^6')
    4
    >>> eval_expr('2**6')
    64
    >>> eval_expr('1 + 2*3**(4^5) / (6 + -7)')
    -5.0
    """
    return eval_(ast.parse(expr, mode='eval').body)

def eval_(node):
    if isinstance(node, ast.Num): # <number>
        return node.n
    elif isinstance(node, ast.BinOp): # <left> <operator> <right>
        return operators[type(node.op)](eval_(node.left), eval_(node.right))
    elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
        return operators[type(node.op)](eval_(node.operand))
    else:
        raise TypeError(node)

def load_wmap(path, inverse=False):
    with open(path) as f:
        d = dict(line.strip().split(None, 1) for line in f)
        if inverse:
            d = dict(zip(d.values(), d.keys()))
        for (s, i) in [('<s>', '1'), ('</s>', '2')]:
            if not s in d or d[s] != i:
                logging.warning("%s has not ID %s in word map %s!" % (s, i, path))
        return d

parser = argparse.ArgumentParser(description='Swap word indices in a word map. In combination with --range, it can be applied '
                                 'to a range of indices. '
                                 'Usage: python swap_wmap_indices.py -r 1:100 -m wmap.de -f i -t 2*i > new_wmap')
parser.add_argument('-1','--expr1', help='Mathematical term specifying one side of the swap. Can contain variable i',
                    required=True)
parser.add_argument('-2','--expr2', help='Mathematical term specifying the other side of the swap. Can contain variable i',
                    required=True)
parser.add_argument('-r','--range', help='Range for variable i. Format <from>:<to> (both inclusive)',
                    required=False)
parser.add_argument('-m','--wmap', help='Word map to apply (format: see -i parameter)',
                    required=True)
parser.add_argument('-i','--inverse_wmap', help='Use this argument to use word maps with format "id word".'
                    ' Otherwise the format "word id" is assumed', action='store_true')
args = parser.parse_args()

wmap = load_wmap(args.wmap, args.inverse_wmap)
inv_wmap = dict(zip(wmap.values(), wmap.keys()))

iter_i = range(1,2)
if args.range:
    f,t = args.range.split(':')
    iter_i = range(int(f), int(t)+1)

for i in iter_i:
    f_idx = str(eval_expr(args.expr1.replace('i', str(i))))
    t_idx = str(eval_expr(args.expr2.replace('i', str(i))))
    tmp = inv_wmap[f_idx]
    inv_wmap[f_idx] = inv_wmap[t_idx]
    inv_wmap[t_idx] = tmp


for idx,word in sorted(inv_wmap.iteritems(), key=lambda it: int(it[0])):
    print("%s %s" % (word,idx))
