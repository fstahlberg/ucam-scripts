# coding=utf-8
r"""This script reads a JSON file produced by SGNMT's
extract_scores_along_reference.py script, and computes predictor 
weights by trying to move the position of the reference word as far
up as possible at each time step.
"""

import logging
import argparse
import sys
import json
import numpy as np
import itertools

parser = argparse.ArgumentParser(description='Find predictor weights based on scores_along_reference JSON.')
parser.add_argument('-j','--json', required=True, help='Input json file.')
parser.add_argument('-v','--vocab_size', required=True, type=int, help='Vocabulary size.')
parser.add_argument('-d','--delta', default=4.0, help='Number of interpolation steps per iteration.')
parser.add_argument('-i','--iterations', default=7, help='Number of iterations.')
parser.add_argument('-n','--num_experts', default=-1, type=int, help='Number of predictors (take first n if positive).')
args = parser.parse_args()
logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s')

data = []

def create_data_points(d):
  ret = []
  for ref_word, unk_scores, posteriors in zip(
          d["trg_sentence"], d["unk_scores"], d["posteriors"]):
    scores = np.tile(np.array(unk_scores, dtype=np.float32), (args.vocab_size, 1))
    # Scores has shape [vocab_size, n_predictors], fill it
    for col, posterior in enumerate(posteriors):
      if isinstance(posterior, list):
        scores[:len(posterior),col] = posterior
      else:
        for  w, s in posterior.iteritems():
          scores[int(w),col] = s
    if args.num_experts > 0:
      scores = scores[:, :args.num_experts]
    ret.append((ref_word, scores))
  return ret

#def eval_data_point(weights, score_matrices, ref_words):
#  weights = np.array(weights)
#  scores = np.dot(score_matrices, weights)
#  ref_scores = scores[data_indices, ref_words]
#  cost = np.sum(scores >=  np.expand_dims(ref_scores, axis=1))
#  return cost

def eval_data_point(weights, data):
  weights = np.array(weights, dtype=np.float32)
  cost = 0
  for ref_word, score_matrix in data:
    scores = np.dot(score_matrix, weights)
    ref_score = scores[ref_word]
    cost += (scores >= ref_score).sum()
  return cost

def generate_eval_points(centers, max_diff, pos=0):
  step_size = max_diff * 2.0 / args.delta
  ranges = [np.arange(max(c - max_diff, 0.0), min(1.0, c + max_diff) + 0.000001, step_size) 
                for c in centers]
  for weights in itertools.product(*ranges):
    yield weights

logging.info("Loading JSON file %s..." % args.json)

num_sentences = 0
with open(args.json) as f:
  #for d in json.load(f):
  #  data.extend(create_data_points(d))
  # Following code is more memory-efficient, but only works for SGNMT's JSON files
  first_line = True
  json_data = []
  for line in f:
    if first_line:
      first_line = False
      continue
    if line[:1] == '}':
      json_data.append('}')
      data.extend(create_data_points(json.loads(''.join(json_data))))
      json_data = []
      num_sentences += 1
      logging.info("Loaded %d sentences" % num_sentences)
    else:
      json_data.append(line)

#score_matrices = np.stack([d[1] for d in data])
#ref_words = np.array([d[0] for d in data])
#data_indices = np.arange(score_matrices.shape[0])
#del data
#n_preds = score_matrices.shape[-1]
#logging.info("Data shape: %s" % (score_matrices.shape,))

n_preds = data[0][1].shape[1]
logging.info("Loaded %d data points with %d predictors" % (len(data), n_preds))
  
max_diff = 0.5
best_cost = float("inf")
best_weights = [0.5] * n_preds
for it in xrange(args.iterations):
  logging.info("Staring iteration %d around %s +-%f..." % (it, best_weights, max_diff))
  for weights in generate_eval_points(best_weights, max_diff):
    #cost = eval_data_point(weights, score_matrices, ref_words)
    cost = eval_data_point(weights, data)
    if cost < best_cost:
      best_weights = weights
      best_cost = cost
      logging.info("Found new best weights: %s (cost: %d)" % (best_weights, best_cost))
  max_diff = 2 * max_diff / args.delta


