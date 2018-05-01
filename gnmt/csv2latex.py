'''
This script creates a heat map in form of a latex table which 
visualizes an alignment matrix in csv format
'''
import argparse
import operator
import sys

parser = argparse.ArgumentParser(description='Reads an alignment matrix from stdin '
                            'and creates latex code which displays it as heat map.')
parser.add_argument('-s','--source', help='File with source sentences', required=True)
parser.add_argument('-t','--target', help='File with target sentences', required=True)
parser.add_argument('-i','--index', help='Line number of sentence pair', type=int, required=True)
args = parser.parse_args()

with open(args.source) as f: 
    src_sen = f.readlines()[args.index].strip().replace('&', '\\&').split()
with open(args.target) as f: 
    trg_sen = f.readlines()[args.index].strip().replace('&', '\\&').split()

src_len = len(src_sen)
trg_len = len(trg_sen)

src_pos = 0
weights = []
for line in sys.stdin:
    weight_line = [0.0] * trg_len
    for trg_pos,weight in enumerate(line.strip().split()):
        weight_line[trg_pos] = float(weight)
    weights.append(weight_line)
while len(weights) < src_len:
    weights.append([0.0] * trg_len)

print('\\documentclass[a4paper]{article}')
print('\\usepackage[utf8]{inputenc}')
print('\\usepackage{rotating}')
print('\\usepackage[table]{xcolor}')
print('\\begin{document}')
print('')

print('\\begin{tabular}{l %s}' % ('l'*trg_len))
print('& \\begin{sideways}%s\end{sideways} \\\\' % '\\end{sideways} & \\begin{sideways}'.join(trg_sen))
for src_pos,weight_line in enumerate(weights):
    colors = ['{\\cellcolor[gray]{%f}}' % (1.0-w) for w in weight_line]
    print("%s & %s \\\\" % (src_sen[src_pos], ' & '.join(colors)))
                            

print('\\end{tabular}')
print('\\end{document}')

