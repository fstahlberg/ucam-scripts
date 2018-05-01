# coding=utf-8
r"""Concatenates features from multiple n-best lists.
"""

import sys
import collections

additional_feats = []

for path in sys.argv[2:]:
  feats = collections.defaultdict(dict)
  with open(path, "r") as f:
    for line in f:
      parts = [s.strip() for s in line.split("|")]
      feats[parts[0]][parts[3]] = parts[6]
  additional_feats.append(feats)


with open(path, "r") as f:
  for line in f:
    parts = [s.strip() for s in line.split("|")]
    print("%s ||| %s ||| %s ||| %s" % (
      parts[0],
      parts[3],
      " ".join([parts[6]] + [feats[parts[0]][parts[3]] for feats in additional_feats]),
      parts[9]))

