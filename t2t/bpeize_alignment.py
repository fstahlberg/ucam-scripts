# coding=utf-8
r"""Converts word level alignments to BPE level alignments by creating
alignment links between BPE tokens if they belong to word pairs which are
aligned to each other. The format of the alignments is:
i1 j1 i2 j2 i3 j3 ... iK jK

where i/j are positions of the src/trg sentences, starting at 0.
"""

import logging
import argparse
import sys

parser = argparse.ArgumentParser(description='Converts word-alignments to BPE-alignments.')
parser.add_argument('-ss','--src_sentences', help='Source sentences (BPE, indexed).', required=True)
parser.add_argument('-ts','--trg_sentences', help='Target sentences (BPE, indexed).', required=True)
parser.add_argument('-sw','--src_wmap', help='Source word map.', required=True)
parser.add_argument('-tw','--trg_wmap', help='Target word map.', required=True)
args = parser.parse_args()

with open(args.src_wmap) as f:
  src_wmap = dict(reversed(l.strip().split(None, 1)) for l in f)

with open(args.trg_wmap) as f:
  trg_wmap = dict(reversed(l.strip().split(None, 1)) for l in f)

def get_word2bpe_map(line, wmap):
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
  return word2bpe_map

with open(args.src_sentences) as src_reader:
  with open(args.trg_sentences) as trg_reader:
    for src, trg, al in zip(src_reader, trg_reader, sys.stdin):
      src_map = get_word2bpe_map(src, src_wmap)
      trg_map = get_word2bpe_map(trg, trg_wmap)
      bpe_al_links = []
      al_links = al.replace("-", " ").strip().split()
      for idx in xrange(0, len(al_links), 2):
        src_word = int(al_links[idx])
        trg_word = int(al_links[idx+1])
        for src_bpe in src_map[src_word]:
          for trg_bpe in trg_map[trg_word]:
            bpe_al_links.append("%d %d" % (src_bpe, trg_bpe))
      print(" ".join(bpe_al_links))

