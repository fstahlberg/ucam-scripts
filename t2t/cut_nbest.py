# coding=utf-8
r"""Like command line cut but for n-best list features
"""

import sys

indices = []
for p in sys.argv[1].split(","):
  if "-" in p:
    f,t = p.split("-")
    indices.extend(range(int(f)-1, int(t)))
  else:
    indices.append(int(p)-1)

for line in sys.stdin:
    parts = [s.strip() for s in line.split("|")]
    feats = parts[6].split()
    print("%s ||| %s ||| %s ||| %s" % (
      parts[0],
      parts[3],
      " ".join(["%s %s" % (feats[i*2], feats[i*2+1]) for i in indices]),
      parts[9]))

