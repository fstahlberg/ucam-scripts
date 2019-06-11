# coding=utf-8
r"""Add word-level noise to BPE indexed data following

https://gist.github.com/edunov/d67d09a38e75409b8408ed86489645dd
https://arxiv.org/pdf/1808.09381.pdf
"""

import argparse
import sys
import numpy as np
import random

parser = argparse.ArgumentParser(description='Add noise')
parser.add_argument('-wd', help='Word dropout', default=0.1, type=float)
parser.add_argument('-wb', help='Word blank', default=0.1, type=float)
parser.add_argument('-sk', help='Shufle k words', default=3, type=int)
parser.add_argument('-wmap', help='Word map', required=True)
parser.add_argument('-blank', help='Blank symbol sequence', default='3 4')
args = parser.parse_args()

def word_shuffle(s, sk):
  noise = np.random.rand(len(words)) * sk
  order = np.arange(len(words)-0.1) + noise
  perm = np.argsort(order)
  return [words[i] for i in perm]

def word_dropout(words, wd):
  keep = np.random.rand(len(words))
  res = [word for i, word in enumerate(words) if keep[i] > wd ]
  if not res:
    return [words[random.randint(0, len(words)-1)]]
  return res

def word_blank(words, wb, blank):
  keep = np.random.rand(len(words))
  return [word if keep[i] > wb else blank for i, word in enumerate(words)]

eow_symbols = set()
with open(args.wmap) as f:
  for line in f:
    w, idx = line.strip().split()
    if w[-4:] == "</w>":
      eow_symbols.add(idx)
blank = args.blank.split()

for line in sys.stdin:
  subwords = line.strip().split()
  words = [[]]
  for subword in subwords:
    words[-1].append(subword)
    if subword in eow_symbols:
      words.append([])
  if not words[-1]:
    words.pop()
  if words:
    words = word_shuffle(words, args.sk)
    words = word_dropout(words, args.wd)
    words = word_blank(words, args.wb, blank)
  print(" ".join(subword for word in words for subword in word))

