# coding=utf-8
r"""Selects lines from a text file."""

import argparse
import sys

parser = argparse.ArgumentParser(description='Selects lines from a text file 0-indexed line numbers from stdin.')
parser.add_argument('-i','--input_filename', help='Text file.', required=True)
args = parser.parse_args()

with open(args.input_filename) as f:
  txt = [line for line in f]

for line_number in sys.stdin:
  sys.stdout.write(txt[int(line_number.strip())])

