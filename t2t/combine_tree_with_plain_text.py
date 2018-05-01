# coding=utf-8
r"""Merges a syntax tree with plain text, keeping plain text tokenization."""

import logging
import argparse
import sys

parser = argparse.ArgumentParser(description='Applies the tokenization given in the plain '
    'text file to a syntax tree.')
parser.add_argument('-p','--plain', help='Plain text file.', required=True)
parser.add_argument('-t','--tree', help='Tree text file.', required=True)
args = parser.parse_args()

with open(args.plain) as plain_handler:
  with open(args.tree) as tree_handler:
    for plain_line, tree_line in zip(plain_handler, tree_handler):
      plain_tokens = plain_line.strip().split()
      tree_tokens = tree_line.replace(")", " ) ").strip().split()
      plain_pos = 0
      combined_tokens = []
      for tree_token in tree_tokens:
        if '(' in tree_token or ')' in tree_token:
          combined_tokens.append("##%s##" % tree_token)
        else:
          while tree_token:
            plain_token = plain_tokens[plain_pos].replace("</w>", "")
            if tree_token[:len(plain_token)] != plain_token:
              sys.exit("Raw text does not match!")
            combined_tokens.append(plain_tokens[plain_pos])
            tree_token = tree_token[len(plain_token):]
            plain_pos += 1
      print(' '.join(combined_tokens))


