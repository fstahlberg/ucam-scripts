# coding=utf-8
r"""Converts an nbest list in Moses format to plain text files.
"""

import logging
import argparse
import sys

parser = argparse.ArgumentParser(description='Converts an nbest list to plain text files.')
parser.add_argument('-is','--src_input', help='Source input sentences.', required=True)
parser.add_argument('-it','--trg_input', help='Target input sentences (nbest list).', required=True)
parser.add_argument('-os','--src_output', help='Source output sentences.', required=True)
parser.add_argument('-ot','--trg_output', help='Target output sentences.', required=True)
args = parser.parse_args()


with open(args.src_input, "r") as src_reader:
  src_sentences = [line.strip() for line in src_reader]

with open(args.trg_input, "r") as trg_reader:
  with open(args.src_output, "w") as src_writer:
    with open(args.trg_output, "w") as trg_writer:
      for nbest_str in trg_reader:
        nbest_parts = nbest_str.split("|")
        src_writer.write("%s\n" % src_sentences[int(nbest_parts[0].strip())])
        trg_writer.write("%s\n" % nbest_parts[3].strip())


