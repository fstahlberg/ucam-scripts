# coding=utf-8
r"""This script reads indexed data from /dev/stdin which either corrsponds
to a linear parse tree or the output of a layer-by-layer model. It produces
one parse tree per line in text format as expected by the EVALB evaluation
tool.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Dependency imports

from tensor2tensor.data_generators import text_encoder

import tensorflow as tf
import re

from os import sys, path
sys.path.append(path.dirname(path.abspath(__file__)))
import ptb_helper


EOS_ID = 1

tf.flags.DEFINE_string("output_encoder", "subword",
                       "'subword': SubwordTextEncoder\n"
                       "'token': TokenTextEncoder")
tf.flags.DEFINE_string("vocab_filename", "",
                       "TokenTextEncoder or SubwordTextEncoder vocabulary file")
tf.flags.DEFINE_string("input_format", "layerbylayer_pop", "This parameter controls "
                       "how the parse trees are integrated in the TFRecord.\n"
                       " 'layerbylayer': For layer-by-layer models.\n"
                       " 'layerbylayer_pop': layer-by-layer with POP control "
                       " symbols for monotone attention on previous layer.\n"
                       " 'flat_starttagged': Linearised tree, '(' tagged.\n"
                       " 'flat_nt_starttagged': Linearised tree without terminals.\n"
                       " 'flat_bothtagged': Linearised tree, '(' and ')' tagged.\n")
tf.flags.DEFINE_string("output_format", "evalb", "'evalb' for parse trees and "
                       "'plain' for terminals only.")
tf.flags.DEFINE_boolean("layerbylayer_cut_at_terminal", True, "If true, we prune "
                       "subtrees under terminals. Otherwise, do not change the "
                        "original layer-by-layer output.")
tf.flags.DEFINE_boolean("postprocess_tree", True, "If true, fix common problems with "
                       "the output being passed through to evalb")
tf.flags.DEFINE_string("eol", "add", "'pad' or 'add', see SGNMT config.")

FLAGS = tf.flags.FLAGS

# Sanity checks
if FLAGS.input_format not in ['layerbylayer', 'layerbylayer_pop', 'flat_starttagged', 
                              'flat_bothtagged', 'flat_nt_starttagged']:
  tf.logging.error("Unknown input format!")
  exit()
if FLAGS.output_format not in ['evalb', 'plain']:
  tf.logging.error("Unknown output format!")
  exit()
if FLAGS.output_encoder not in ['subword', 'token']:
  tf.logging.error("Unknown output encoder!")
  exit()


class Writer(object):

  def __init__(self, encoder):
    self.encoder = encoder
    self.is_layerbylayer = FLAGS.input_format in ['layerbylayer', 'layerbylayer_pop']
    self.is_nt_only = FLAGS.input_format in ['flat_nt_starttagged']
    with open(FLAGS.vocab_filename) as f:
      self.nt_lookup = dict([(idx, s.strip()[1:-1]) for idx, s in enumerate(f)
                          if s.startswith("'##")])
      if self.is_layerbylayer:
        if FLAGS.eol == "add":
          self.eol_id = idx + 1
        else:
          self.eol_id = 0
        tf.logging.info("End-of-layer ID: %d" % self.eol_id)
      tf.logging.info("Found %d non-terminal labels.", len(self.nt_lookup))

  def write(self, tokens):
    raise NotImplementedError()

  def get_nt_label(self, token):
    lbl = self.nt_lookup[token][2:-2]
    if lbl == "(ROOT":
      return "(TOP"
    if lbl == "ROOT":
      return "TOP"
    if lbl[-1:] == ")":
      return ")"
    return lbl


class PlainWriter(Writer):

  def write(self, tokens):
    if self.is_layerbylayer:
      try:
        # Remove everything before the last '0' (end-of-layer)
        tokens = tokens[len(tokens) - tokens[::-1].index(0):]
      except:
        pass # Use all tokens if no end-of-layer found
    # Filter non-terminals
    terminals = [t for t in tokens if t not in self.nt_lookup]
    return self.encoder.decode(terminals)


class Node(object):
  def __init__(self, label, in_last_layer=False):
    self.label = label
    self.children = []
    self.in_last_layer = in_last_layer

  def __repr__(self):
    if self.children:
      return "(%s %s)" % (self.label, ' '.join([str(c) for c in self.children]))
    return self.label


class EvalbWriter(Writer):
  def __init__(self, encoder):
    super(EvalbWriter, self).__init__(encoder)
    self.tokenizer = ptb_helper.SimpleTokenizer()
    for idx, lbl in self.nt_lookup.iteritems():
      if lbl == "##ROOT##":
        self.root_id = idx
      if lbl == "##POP##":
        self.pop_id = idx

  def write(self, tokens):
    if self.is_layerbylayer:
      return self.write_layerbylayer(tokens)
    return self.write_flat(tokens)

  def write_layerbylayer(self, tokens):
    last_layer = [] 
    layers = [last_layer]
    for t in tokens:
      if t == self.eol_id: # End-of-layer symbol
        last_layer.append(EOS_ID)
        last_layer = []
        layers.append(last_layer)
      else:
        last_layer.append(t)
    last_layer.append(EOS_ID)
    root = Node(self.root_id)
    target_roots = [root, root]
    root_is_nt = True
    for n_layer, layer in enumerate(layers):
      in_last_layer = n_layer == len(layers) - 1
      target_root_pointer = 0
      next_target_roots = []
      for t in layer:
        if t == self.pop_id:
          target_root_pointer += 1
        else:
          root_is_nt = target_roots[target_root_pointer].label in self.nt_lookup
          n = Node(t, in_last_layer=in_last_layer)
          target_roots[target_root_pointer].children.append(n)
          next_target_roots.append(n)
      n.in_last_layer = False  # Mark EOS for pruning
      target_roots = next_target_roots
    self.postprocess_tree(root)
    return self.linearize(root)

  def postprocess_tree(self, root):
    """Removes subtrees which do not end up in in_last_layer nodes, 
    cut at terinals.
    """
    def remove_dead_ends(n):
      if n.in_last_layer:
        if not self.encoder.decode([n.label]).strip():
          # Prune nodes with whitespace
          return False
        return True
      n.children = [c for c in n.children if remove_dead_ends(c)]
      if n.children:
        return True
      return False

    def cut_at_terminal(n):
      if n.label in self.nt_lookup or n.label == EOS_ID:
        for c in n.children:
          cut_at_terminal(c)
      else:
        n.children = []

    if FLAGS.postprocess_tree:
      remove_dead_ends(root)
    if FLAGS.layerbylayer_cut_at_terminal:
      cut_at_terminal(root)
    if FLAGS.postprocess_tree:
      collapse_identities(root)

  def linearize(self, root):
    pending_terminals = []
    try:
      str_tokens = ["(%s" % self.get_nt_label(root.label)]
    except KeyError: # Terminal symbol at root
      str_tokens = ["(%s" % self.decode([root.label])]
    if any(c.children for c in root.children): # If any child has a child
      for c in root.children:
        c_lin = self.linearize(c)
        if not c_lin.startswith("("):
          c_lin = "(<uni> %s)" % c_lin
        str_tokens.append(c_lin)
    else: # No subtrees => flat combination
      str_tokens.append(self.decode([c.label for c in root.children]))
    linear = " ".join(str_tokens) + ")"
    linear = linear.replace(" )", ")").replace("  ", " ")
    return ptb_helper.clean_up_linearization(linear)

  def decode(self, tokens):
    for token in tokens:
      if token in self.nt_lookup:
        return "(%s <dummy>)" % self.nt_lookup[token][2:-2]
    tok_str = self.tokenizer.tokenize(self.encoder.decode(tokens))
    # insert blanks
    tok_str = tok_str.replace(",", " , ")
    tok_str = tok_str.replace(".", " . ")
    tok_str = tok_str.replace("*", " * ")
    tok_str = re.sub(r"\* *([A-Z]+) *\*", r"*\1*", tok_str, flags=re.UNICODE)
    tok_str = tok_str.strip()
    if " " in tok_str:
      return " ".join(["(<uni> %s)" % t for t in tok_str.split()])
    return tok_str

  def write_flat(self, tokens):
    str_tokens = []
    pending_terminals = []
    for token in tokens:
      if token in self.nt_lookup:
        if pending_terminals:
          str_tokens.append(self.decode(pending_terminals))
        str_tokens.append(self.get_nt_label(token))
        pending_terminals = []
      else:
        pending_terminals.append(token)
    if pending_terminals:
      str_tokens.append(self.decode(pending_terminals))
    linear = " ".join(str_tokens)
    n_opening = linear.count("(")
    n_closing = linear.count(")")
    if n_opening < n_closing:
      tf.logging.warn("Unbalanced brackets: add %d opening.", 
                      n_closing - n_opening)
      linear = "(TOP " * (n_closing - n_opening) + linear    
    if n_opening > n_closing:
      linear = re.sub(r"\(([^ ]+) *$", r"(\1 \1", linear)
      tf.logging.warn("Unbalanced brackets: add %d closing.", 
                      n_opening - n_closing)
      linear += " ) " * (n_opening - n_closing)
    linear = linear.strip()
    if self.is_nt_only:
      # Do not postprocess or clean up, but insert <placeholder>
      linear = re.sub(r"\(([^ )]+) *\)", r"(\1 <placeholder>)",  linear)
      linear = re.sub(r" +\)", ")", linear)
      linear = re.sub(r"  +", " ", linear)
      return linear
    try:
      tmp, _ = parse(linear.strip().split())
      tree = tmp[0]
      collapse_identities(tree)
      linear = str(tree)
    except:
      tf.logging.warn("Could not parse tree.")
    linear = re.sub(r" +\)", ")", linear)
    linear = re.sub(r"  +", " ", linear)
    return ptb_helper.clean_up_linearization(linear)


def collapse_identities(n):
  while len(n.children) == 1 and n.children[0].label == n.label:
    n.children = n.children[0].children
  for c in n.children:
    collapse_identities(c)


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


def main(_):
  """Convert a file to examples."""
  if FLAGS.output_encoder == "subword":
    encoder = text_encoder.SubwordTextEncoder(
        FLAGS.vocab_filename)
  elif FLAGS.output_encoder == "token":
    encoder = text_encoder.TokenTextEncoder(FLAGS.vocab_filename)
  elif FLAGS.output_encoder == "byte":
    encoder = text_encoder.ByteTextEncoder()
  else:
    tf.logging.error("Unknown encoder")
  if FLAGS.output_format =="evalb":
    writer = EvalbWriter(encoder)
  elif FLAGS.output_format =="plain":
    writer = PlainWriter(encoder)
  tf.logging.set_verbosity(tf.logging.INFO)
  for line in sys.stdin:
    tokens = [int(i) for i in line.strip().split()]
    print(writer.write(tokens))


if __name__ == "__main__":
  tf.app.run()
