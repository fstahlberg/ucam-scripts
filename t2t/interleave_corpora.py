# coding=utf-8
r"""Mixes and shuffles corpora, but shuffling is restricted with
respect to oversampling: Oversampled corpora are shuffled only once
and then self-concatenated and interleaved with other corpora. This
makes sure that duplicates are separated by the full corpus.
"""

import argparse
import sys
from collections import defaultdict
import numpy as np
import random

parser = argparse.ArgumentParser(description='Mixes and shuffles corpora')
parser.add_argument('-si','--source_input_files', help='Comma-separated list of plain text files with source sentences.', required=True)
parser.add_argument('-ti','--target_input_files', help='Comma-separated list of plain text files with target sentences.', required=True)
parser.add_argument('-so','--source_output_file', help='Output plain text file with source sentences.', required=True)
parser.add_argument('-to','--target_output_file', help='Output plain text file with target sentences.', required=True)
args = parser.parse_args()

oversampling = defaultdict(lambda: 0)

for src_in_file, trg_in_file in zip(args.source_input_files.split(","), args.target_input_files.split(",")):
  oversampling["%s,%s" % (src_in_file, trg_in_file)] += 1

sentences = []
indices = []
corpus_id = 0

for key, multiplier in oversampling.iteritems():
  corpus_sentences = []
  src_file, trg_file = key.split(",")
  with open(src_file) as src_reader:
    with open(trg_file) as trg_reader:
      for src_line, trg_line in zip(src_reader, trg_reader):
        corpus_sentences.append((src_line, trg_line))
  random.shuffle(corpus_sentences)
  n = len(corpus_sentences)
  print("Adding %d x %d = %d sentences from %s" % (n, multiplier, n*multiplier, key))
  indices.append(np.full((n*multiplier,), corpus_id, dtype=np.int8))
  sentences.append(corpus_sentences)
  corpus_id += 1

all_indices = np.concatenate(indices)
np.random.shuffle(all_indices)
corpus_iter = [0] * len(sentences)
corpus_mod = [len(s) for s in sentences]

print("Writing %d sentences..." % all_indices.shape)
with open(args.source_output_file, "w") as src_writer:
  with open(args.target_output_file, "w") as trg_writer:
    for corpus_id in all_indices:
      src_line, trg_line =  sentences[corpus_id][corpus_iter[corpus_id]]
      src_writer.write(src_line)
      trg_writer.write(trg_line)
      corpus_iter[corpus_id] = (corpus_iter[corpus_id] + 1) % corpus_mod[corpus_id]


