r"""Expected format
123 234 345|12 3221 22
"""

import argparse
import sys

parser = argparse.ArgumentParser(description='Removes entries where one side is empty, outputs left side')
parser.add_argument('-l','--left', help='Left sentences', required=True)
parser.add_argument('-r','--right', help='Right sentences', required=True)
args = parser.parse_args()

with open(args.left) as left_reader:
  with open(args.right) as right_reader:
    for left_line, right_line in zip(left_reader, right_reader):
      if left_line.strip() and right_line.strip():
        sys.stdout.write(left_line)

