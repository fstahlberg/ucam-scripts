# coding=utf-8
r"""Converts BPE level alignments to word level alignments by creating
alignment links between words if one of their BPE tokens are aligned
to each other. The format of the alignments is:
i1 j1 i2 j2 i3 j3 ... iK jK

where i/j are positions of the src/trg sentences, starting at 0.
"""

import logging
import argparse
import sys

parser = argparse.ArgumentParser(description='Converts BPE-alignments to word-alignments.')
parser.add_argument('-ss','--src_sentences', help='Source sentences (BPE, indexed).', required=True)
parser.add_argument('-ts','--trg_sentences', help='Target sentences (BPE, indexed).', required=True)
parser.add_argument('-sw','--src_wmap', help='Source word map.', required=True)
parser.add_argument('-tw','--trg_wmap', help='Target word map.', required=True)
args = parser.parse_args()

with open(args.src_wmap) as f:
  src_wmap = dict(reversed(l.strip().split(None, 1)) for l in f)

with open(args.trg_wmap) as f:
  trg_wmap = dict(reversed(l.strip().split(None, 1)) for l in f)

def get_bpe2word_map(line, wmap):
  words = line.strip().split()
  mapped_words = [wmap[w] for w in words]
  lengths = [0]
  for w in mapped_words:
    lengths[-1] += 1
    if "</w>" in w:
      lengths.append(0)
  next_bpe_pos = 0
  word2bpe_map = []
  for l in lengths[:-1]:
    bpe_ids = []
    for _ in xrange(l):
      bpe_ids.append(next_bpe_pos)
      next_bpe_pos += 1
    word2bpe_map.append(bpe_ids)
  bpe2word_map = {}
  for word_pos, bpe_poss in enumerate(word2bpe_map):
    for bpe_pos in bpe_poss:
      bpe2word_map[bpe_pos] = word_pos
  return bpe2word_map

with open(args.src_sentences) as src_reader:
  with open(args.trg_sentences) as trg_reader:
    for src, trg, al in zip(src_reader, trg_reader, sys.stdin):
      src_map = get_bpe2word_map(src, src_wmap)
      trg_map = get_bpe2word_map(trg, trg_wmap)
      bpe_al_links = al.replace("-", " ").strip().split()
      src_map[max(src_map.iterkeys())+1] = max(src_map.itervalues())+1
      al_links = set()
      for idx in xrange(0, len(bpe_al_links), 2):
        al_links.add((src_map[int(bpe_al_links[idx])], 
                      trg_map[int(bpe_al_links[idx+1])]))
      print(" ".join("%d-%d" % link for link in sorted(al_links)))

