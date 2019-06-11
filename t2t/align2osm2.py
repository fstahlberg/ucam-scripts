# coding=utf-8
r"""Converts alignments to operation sequences v2. The format of the alignments is:
i1 j1 i2 j2 i3 j3 ... iK jK

where i/j are positions of the src/trg sentences, starting at 0.

The OSNMT2 model is monotone on the target side and jumps in the source
sentence:

EOP: See EOP type
JUMP_FWD: Jump one token forward.
JUMP_BWD: Jump one token backward.

Alignments are cleaned from alignment links which do not fit into this model:

- If one target word is aligned to multiple source words, we only keep the first
  alignment link.
- If a target word is not aligned to any source word, copy the alignment information 
  from the preceeding target word. If we are at sentence begin, copy it from the
  following target word.
"""

import logging
import argparse
import sys

parser = argparse.ArgumentParser(description='Converts alignments to OSM sequences.')
parser.add_argument('-s','--source', help='Source sentences.', required=True)
parser.add_argument('-t','--target', help='Target sentences.', required=True)
parser.add_argument('-a','--alignments', help='Alignments.', required=True)
parser.add_argument('-e','--eop_type', help="Defines the semantic of EOP.\n"
                    "- 'close' EOP closes the current source token, JMP will skip it from now on.\n" 
                    "- 'open' Source tokens are automatically closed unless EOP is produced directly before.\n" 
                    "- 'no' Never close source tokens, never output EOP.\n", default='close')
args = parser.parse_args()

def preprocess_alignment(al_links, trg_len):
  al_links.sort(key=lambda x: (x[1], -x[0]))  # Sort ascending by target pos
  trg2src = [-1 for _ in xrange(trg_len)]
  for src_pos, trg_pos in al_links:
    if trg2src[trg_pos] == -1:
      trg2src[trg_pos] = src_pos
  # Align unaligned target words
  prev_src_pos = al_links[0][0]
  for trg_pos in xrange(trg_len):
    if trg2src[trg_pos] == -1:
      trg2src[trg_pos] = prev_src_pos
    prev_src_pos = trg2src[trg_pos]
  clean_al_links = [(src_pos, trg_pos) for trg_pos, src_pos in enumerate(trg2src)]
  return clean_al_links


def generate_operations(src, trg, trg2src):
  print(src)
  print(trg)
  print(trg2src)
  ops = []
  closed = [False] * len(src)
  fert = [0] * len(src)
  for trg_pos, src_pos in enumerate(trg2src):
    fert[src_pos] += 1
  head = 0
  for trg_pos, src_pos in enumerate(trg2src):
    incr = 1 if src_pos > head else -1
    jmp = 'JMP_FWD' if src_pos > head else 'JMP_BWD'
    while head != src_pos:
      if not closed[head]:
        ops.append(jmp)
      head += incr
    
    if args.eop_type == "open" and fert[src_pos] > 1:
      ops.append("EOP")
    fert[src_pos] -= 1
    ops.append(trg[trg_pos])
    if args.eop_type == "close":
      if fert[src_pos] == 0:
        ops.append("EOP")
    if args.eop_type != "no" and fert[src_pos] == 0:
      closed[src_pos] = True
  print(ops)    
  sys.exit()
  return ops

with open(args.source) as src_reader:
  with open(args.target) as trg_reader:
    with open(args.alignments) as al_reader:
      sen_idx = 0
      for src, trg, al in zip(src_reader, trg_reader, al_reader):
        #print("\n SENTENCE %d -------------------------" % sen_idx)
        sen_idx += 1
        src = src.strip().split()
        trg = trg.strip().split()
        al = map(int, al.strip().split())
        al_links = [(al[i], al[i+1]) for i in xrange(0, len(al), 2)]
        al_links = preprocess_alignment(al_links, len(trg))
        #print(" ".join(["%s-%s" % a for a in al_links]))
        #continue
        trg2src = [-1] * len(trg)
        for src_pos, trg_pos in al_links:
          trg2src[trg_pos] = src_pos
        ops = generate_operations(src, trg, trg2src)
        print(" ".join(ops))


