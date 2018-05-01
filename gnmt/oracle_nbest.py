'''
Reorders hypotheses in an n-best list, best BLEU first.

Note that this is just an approximated BLEU score as we use the tokens
of the nbest list.
'''

import logging
import argparse
import sys
import numpy as np
import collections
import math

parser = argparse.ArgumentParser(description='Can be used to compute the oracle BLEU of an nbest list. Reorders '
                                 'hypos best BLEU first.')
parser.add_argument('-r','--reference', help='Path to the reference file', required=True)
args = parser.parse_args()

ref_reader = open(args.reference)



def _get_ngrams(segment, max_order):
  """Extracts all n-grams upto a given maximum order from an input segment.
  Args:
    segment: text segment from which n-grams will be extracted.
    max_order: maximum length in tokens of the n-grams returned by this
        methods.
  Returns:
    The Counter containing all n-grams upto max_order in segment
    with a count of how many times each n-gram occurred.
  """
  ngram_counts = collections.Counter()
  for order in range(1, max_order + 1):
    for i in range(0, len(segment) - order + 1):
      ngram = tuple(segment[i:i+order])
      ngram_counts[ngram] += 1
  return ngram_counts


def compute_bleu(reference_corpus, translation_corpus, max_order=4,
                 smooth=False):
  """Computes BLEU score of translated segments against one or more references.
  Args:
    reference_corpus: list of lists of references for each translation. Each
        reference should be tokenized into a list of tokens.
    translation_corpus: list of translations to score. Each translation
        should be tokenized into a list of tokens.
    max_order: Maximum n-gram order to use when computing BLEU score.
    smooth: Whether or not to apply Lin et al. 2004 smoothing.
  Returns:
    3-Tuple with the BLEU score, n-gram precisions, geometric mean of n-gram
    precisions and brevity penalty.
  """
  matches_by_order = [0] * max_order
  possible_matches_by_order = [0] * max_order
  reference_length = 0
  translation_length = 0
  for (references, translation) in zip(reference_corpus,
                                       translation_corpus):
    reference_length += min(len(r) for r in references)
    translation_length += len(translation)

    merged_ref_ngram_counts = collections.Counter()
    for reference in references:
      merged_ref_ngram_counts |= _get_ngrams(reference, max_order)
    translation_ngram_counts = _get_ngrams(translation, max_order)
    overlap = translation_ngram_counts & merged_ref_ngram_counts
    for ngram in overlap:
      matches_by_order[len(ngram)-1] += overlap[ngram]
    for order in range(1, max_order+1):
      possible_matches = len(translation) - order + 1
      if possible_matches > 0:
        possible_matches_by_order[order-1] += possible_matches

  precisions = [0] * max_order
  for i in range(0, max_order):
    if smooth:
      precisions[i] = ((matches_by_order[i] + 1.) /
                       (possible_matches_by_order[i] + 1.))
    else:
      if possible_matches_by_order[i] > 0:
        precisions[i] = (float(matches_by_order[i]) /
                         possible_matches_by_order[i])
      else:
        precisions[i] = 0.0

  if min(precisions) > 0:
    p_log_sum = sum((1. / max_order) * math.log(p) for p in precisions)
    geo_mean = math.exp(p_log_sum)
  else:
    geo_mean = 0

  ratio = float(translation_length) / reference_length

  if ratio > 1.0:
    bp = 1.
  else:
    bp = math.exp(1 - 1. / ratio)

  bleu = geo_mean * bp

  return (bleu, precisions, bp, ratio, translation_length, reference_length)


def print_cur_sens(cur_id, ref_sen, cur_sens):
    bleus = []
    for sen, _, _ in cur_sens:
        words = sen.strip().split()
        if not words:
            bleu = 0.0
        else:
            bleu, _, _, _, _, _ = compute_bleu([[ref_sen]], [sen.strip().split()])
        bleus.append(bleu)
    for bleu, (sen, feats_str, org_score) in sorted(zip(bleus, cur_sens), key=lambda it: -it[0]):
        print("%d |||%s|||%stotal= %s ||| %f" % (cur_id, sen, feats_str, org_score.strip(), bleu))

cur_id = -1
cur_sens = []
for line in sys.stdin:
    parts = line.split('|')
    this_id = int(parts[0].strip())
    if cur_id != this_id:
        if cur_sens:
            print_cur_sens(cur_id, ref_reader.next().strip().split(), cur_sens)
        cur_sens = []
        cur_id = this_id
    cur_sens.append((parts[3], parts[6], parts[9]))
print_cur_sens(cur_id, ref_reader.next().strip().split(), cur_sens)
