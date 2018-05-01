# coding=utf-8
r"""Modifies syntax trees such that they use the same tokenization as
some reference trees. The syntax trees must be well-formed. This can be
used as preprocessing step to evalb to make sure that all sentences are
scored.
"""

import logging
import argparse
import re
from os import sys, path
sys.path.append(path.dirname(path.abspath(__file__)))
import ptb_helper
sys.setrecursionlimit(10000)

parser = argparse.ArgumentParser(description='Reads syntax trees from stdin and modifies them '
                                 'such that their tokenization is consistent with --references.')
parser.add_argument('-r','--references', help='Trees with reference tokenizations.',
                    required=True)
args = parser.parse_args()
logging.getLogger().setLevel(logging.INFO)

class Node(object):
  def __init__(self, label):
    self.label = label
    self.children = []

  def get_plain(self):
    if self.children:
      return ''.join([c.get_plain() for c in self.children])
    return self.label

  def __repr__(self):
    if self.children:
      return "(%s %s)" % (self.label, " ".join([str(c) for c in self.children]))
    return self.label

def parse(tokens):
  if not tokens[0].startswith("("):
    return [Node(tokens[0])], tokens[1:]
  nodes = []
  while tokens and tokens[0].startswith("("):
    root = Node(tokens[0][1:])
    nodes.append(root)
    children, tokens = parse(tokens[1:])
    root.children = children
    tokens = tokens[1:] # Delete )
  return nodes, tokens

def contains_terminal(node):
  return len(node.children) == 1 and not node.children[0].children

def fill_in_placeholders(root, tokens):
  if root.label == "<placeholder>":
    root.label = tokens[0]
    tokens = tokens[1:]
  for c in root.children:
    tokens = fill_in_placeholders(c, tokens)
  return tokens

def add_rest_tokens(root, rest_tokens):
  # Called when there are more tokens than placeholders
  # Adds the rest tokens to the top node with multiple children
  while len(root.children) == 1:
    root = root.children[0]
  for token in rest_tokens:
    n = Node("<rest>")
    n.children.append(Node(token))
    root.children.append(n)
    
def fix_tokenization(root, tokens, pending_str=""):
  # Breaks if a single ref token covers more than two nodes in the tree
  new_children = []
  for c in root.children:
    if contains_terminal(c):
      terminal_node = c.children[0]
      if len(pending_str) >= len(terminal_node.label):
        pending_str = pending_str[len(terminal_node.label):]
        continue  # Continue without adding this node to new_children
      terminal_node.label = terminal_node.label[len(pending_str):]
      pending_str = ""
      label_length = len(terminal_node.label)
      new_children.append(c)
      if label_length <= len(tokens[0]):
        # If token is foobar & terminal label is foo, set label
        # too foobar and pending_str to bar
        pending_str = tokens[0][label_length:]
        terminal_node.label = tokens[0]
        tokens = tokens[1:]
      else: # subdivide node
        # If token is foo & terminal label if foobar, multiply node
        remaining_label = terminal_node.label[len(tokens[0]):]
        terminal_node.label = tokens[0]
        tokens = tokens[1:]
        while len(tokens[0]) <= len(remaining_label):
          remaining_label = remaining_label[len(tokens[0]):]
          n = Node(c.label)
          n.children = [Node(tokens[0])]
          new_children.append(n)
          tokens = tokens[1:]
        if remaining_label:
          pending_str = tokens[0][len(remaining_label):]
          n = Node(c.label)
          n.children = [Node(tokens[0])]
          new_children.append(n)
          tokens = tokens[1:]
    else:
      tokens, pending_str = fix_tokenization(c, tokens, pending_str)
      if c.children:
        new_children.append(c)
  root.children = new_children
  return tokens, pending_str

with open(args.references) as f:
  for idx, (tree_lin, ref_tree_lin) in enumerate(zip(sys.stdin, f)):
    ref_tokens = re.sub(r"\([^ ]+", " ", 
                        ref_tree_lin).replace(")", " ").strip().split()
    tmp, rest_tokens = parse(tree_lin.replace(")", " ) ").strip().split())
    tree = tmp[0]
    plain = tree.get_plain()
    if re.search(r"^(<placeholder>)+$", plain):  # Simply fill in placeholders
      rest_tokens = fill_in_placeholders(tree, ref_tokens)
      if rest_tokens:
        logging.warn("Not enough placeholders (id %d)!" % idx)
        add_rest_tokens(tree, rest_tokens)
    elif plain != ''.join(ref_tokens):
      logging.warn("Strings do not agree (id %d)" % idx)
      logging.warn("#%s#" % plain)
    else:  # Align tree tokenization with reference tokens
      fix_tokenization(tree, ref_tokens)
    linear = str(tree)
    print(ptb_helper.clean_up_linearization(linear))

