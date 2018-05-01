# coding=utf-8
r"""This script reads a JSON file produced by SGNMT's
extract_scores_along_reference.py script, and computes the best 
interpolation weight at each reference word individually.
"""

import logging
import argparse
import sys
import json
import numpy as np
import itertools

parser = argparse.ArgumentParser(description='Find the best interpolation weights for each word based on scores_along_reference JSON.')
parser.add_argument('-j','--json', required=True, help='Input json file.')
parser.add_argument('-v','--vocab_size', required=True, type=int, help='Vocabulary size.')
parser.add_argument('-d','--delta', default=4.0, help='Number of interpolation steps per iteration.')
parser.add_argument('-i','--iterations', default=4, help='Number of iterations.')
parser.add_argument('-n','--num_experts', default=0, type=int, help='If positive, use only first n experts.')
parser.add_argument('-f', '--full_json', action='store_true', help='Dump full JSON together with predictor scores.')
args = parser.parse_args()
logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s')

data = []

def process_sentence(d):
  all_weights = []
  all_costs = []
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
      scores = scores[:,:args.num_experts]
    # Optimize weights by moving the position in ref_word up in weighted scores
    max_diff = 0.5
    best_cost = float("inf")
    best_weights = [0.5] * scores.shape[1]
    for it in xrange(args.iterations):
      updated = False
      for weights in generate_eval_points(best_weights, max_diff):
        cost = eval_data_point(weights, ref_word, scores)
        if cost < best_cost:
          best_weights = weights
          best_cost = cost
          updated = True
      if not updated:
        break
      max_diff = 2 * max_diff / args.delta
    logging.info("cost=%f weights=%s word=%d" % (best_cost, best_weights, ref_word))
    weights_partition = sum(best_weights)
    all_weights.append(np.array([w / weights_partition for w in best_weights]))
    all_costs.append(best_cost)
  obj = {
      "src_sentence": np.array(d["src_sentence"]),
      "trg_sentence": np.array(d["trg_sentence"]),
      "best_weights": all_weights,
      "best_weights_cost": np.array(all_costs)
  }
  if args.full_json:
    obj["unk_scores"] = d["unk_scores"]
    obj["posteriors"] = d["posteriors"]
  return obj


INDENT = 2
SPACE = " "
NEWLINE = "\n"
def to_json(o, level=0):
    """ Adapted from

    https://stackoverflow.com/questions/21866774/pretty-print-json-dumps 
    """
    ret = ""
    if isinstance(o, dict):
        if level < 2:
            ret += "{" + NEWLINE
            comma = ""
            for k,v in sorted(o.iteritems()):
                ret += comma
                comma = ",\n"
                ret += SPACE * INDENT * (level+1)
                ret += '"' + str(k) + '":' + NEWLINE + SPACE * INDENT * (level+1)
                ret += to_json(v, level + 1)
            ret += NEWLINE + SPACE * INDENT * level + "}"
        else:
            ret += "{" + ", ".join(['"%s": %s' % (str(k), to_json(v, level+1)) 
                   for k,v in sorted(o.iteritems())
               ]) + "}"
    elif isinstance(o, basestring):
        ret += '"' + o + '"'
    elif isinstance(o, list):
        if level < 3:
          ret += "[" + NEWLINE
          comma = ""
          for e in o:
              ret += comma
              comma = ",\n"
              ret += SPACE * INDENT * (level+1)
              ret += to_json(e, level + 1)
          ret += NEWLINE + SPACE * INDENT * level + "]"
        else:
          ret += "[" + ', '.join([to_json(e, level + 1) for e in o]) + "]"
    elif isinstance(o, bool):
        ret += "true" if o else "false"
    elif isinstance(o, int):
        ret += str(o)
    elif isinstance(o, np.float32) or isinstance(o, float):
        ret += '%.7g' % o
    elif isinstance(o, np.ndarray) and np.issubdtype(o.dtype, np.integer):
        ret += "[" + ', '.join(map(str, o.flatten().tolist())) + "]"
    elif isinstance(o, np.ndarray) and np.issubdtype(o.dtype, np.inexact):
        ret += "[" + ','.join(map(lambda x: '%.7g' % x, o.flatten().tolist())) + "]"
    else:
        print(o)
        raise TypeError("Unknown type '%s' for json serialization" % str(type(o)))
    return ret.replace("inf", "Infinity")

def eval_data_point(weights, ref_word, scores):
  weights = np.array(weights, dtype=np.float32)
  weighted_scores = np.dot(scores, weights)
  ref_score = weighted_scores[ref_word]
  eos_score = weighted_scores[1]
  num_better_words = (weighted_scores >= ref_score).sum()
  weighted_scores[ref_word] = float("-inf")
  diff = np.amax(weighted_scores) - ref_score
  return num_better_words + 0.001 * diff + 0.001

def generate_eval_points(centers, max_diff, pos=0):
  step_size = max_diff * 2.0 / args.delta
  ranges = [np.arange(max(c - max_diff, 0.0), min(1.0, c + max_diff) + 0.000001, step_size)[::-1]
                for c in centers]
  for weights in itertools.product(*ranges):
    yield weights

logging.info("Loading JSON file %s..." % args.json)

num_sentences = 0
print("[")
out_comma = ""
with open(args.json) as f:
  first_line = True
  json_data = []
  for line in f:
    if first_line:
      first_line = False
      continue
    if line[:1] == '}':
      json_data.append('}')
      obj = process_sentence(json.loads(''.join(json_data)))
      sys.stdout.write(out_comma + to_json(obj))
      out_comma = ",\n"
      json_data = []
      num_sentences += 1
      logging.info("Processed %d sentences" % num_sentences)
    else:
      json_data.append(line)

sys.stdout.write("\n]")
