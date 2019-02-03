"""Creates an FST which accepts all strings in STDIN
"""

import argparse
import sys

parser = argparse.ArgumentParser(description='Creates an FST in text format which accepts '
                                 'all strings in STDIN. Format: '
                                 'input [| output] [: weight]')
parser.add_argument('-e','--allow_eps', help='If false, ignore all lines in STDIN which '
                    'contain at least one "0"', action='store_true', default=False)
parser.add_argument('-i','--invert_weights', help='If true, multiply all weights by -1', 
                    action='store_true', default=False)
args = parser.parse_args()

next_free_id = 1
for line in sys.stdin:
    parts = line.split(":")
    if len(parts) > 1:
        tapes = parts[0]
        w = float(parts[1].strip())
        if args.invert_weights:
            w *= -1
        weight = " %f" % w
    else:
        tapes = line
        weight = ""
    parts = tapes.split("|")
    input_seq = [int(i) for i in parts[0].strip().split()]
    if len(parts) > 1:
        output_seq = [int(i) for i in parts[1].strip().split()]
    else:
        output_seq = input_seq
    if not args.allow_eps and (
            any([i == 0 for i in input_seq]) or
            any([i == 0 for i in output_seq])):
        continue
    last_id = 0
    for idx in xrange(max(len(input_seq), len(output_seq))):
        print("%d %d %d %d%s" % (last_id,
                                 next_free_id,
                                 0 if idx >= len(input_seq) else input_seq[idx],
                                 0 if idx >= len(output_seq) else output_seq[idx],
                                 weight))
        weight = ""
        last_id = next_free_id
        next_free_id += 1
    print(next_free_id - 1)

