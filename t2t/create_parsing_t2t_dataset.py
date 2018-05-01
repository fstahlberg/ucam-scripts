# coding=utf-8
r"""This script creates T2T datasets for layer-by-layer models or sequence
models on linearised parse trees. The parse trees are loaded from a plain
text file. We expect one parse tree in each line, PTB escaped like given
by the stanford parser, or the original PTB data after processing with

/home/nst/mt126/nlg/parses/ptb/en-ptb16/data/process_v1.0.pl

The data is constructed as follows:
- Terminals are tokenized and indexed with a T2T text_encoder
- Non-terminals are looked up in the vocab file and converted holistically
- The format option decides how the trees are stored in the T2T dataset
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Dependency imports

from tensor2tensor.data_generators import text_encoder

from os import sys, path
sys.path.append(path.dirname(path.abspath(__file__)))
import ptb_helper

import tensorflow as tf

tf.flags.DEFINE_string("output_encoder", "subword",
                       "'subword': SubwordTextEncoder\n"
                       "'token': TokenTextEncoder")
tf.flags.DEFINE_string("vocab_filename", "",
                       "TokenTextEncoder or SubwordTextEncoder vocabulary file")
tf.flags.DEFINE_string("output_filename", "", "output filename")
tf.flags.DEFINE_string("penn_filename", "", "Parse trees, one each line. For "
                       "example the .penn.compact file from lexparser_std.sh")
tf.flags.DEFINE_string("format", "layerbylayer_pop", "This parameter controls "
                       "how the parse trees are integrated in the TFRecord.\n"
                       " 'layerbylayer': For layer-by-layer models.\n"
                       " 'layerbylayer_pop': layer-by-layer with POP control "
                       " symbols for monotone attention on previous layer.\n"
                       " 'flat_starttagged': Linearised tree, '(' tagged.\n"
                       " 'flat_nt_starttagged': Without terminals.\n"
                       " 'flat_endtagged': Linearised tree, ')' tagged.\n"
                       " 'flat_bothtagged': Linearised tree, '(' and ')' tagged.\n")
tf.flags.DEFINE_string("inputs_generator", "tokenized", "How to generate inputs. "
                       "'tokenized' encodes the entire tokenized sentence with T2T, "
                       "'concat' concatenates the encodings of the isolated nodes. "
                       "Use concat if terminals on in- and output need to match exactly.")

FLAGS = tf.flags.FLAGS

# Sanity checks
if FLAGS.format not in ['layerbylayer', 'layerbylayer_pop', 'flat_starttagged', 
                        'flat_nt_starttagged', 'flat_endtagged', 'flat_bothtagged']:
  tf.logging.error("Unknown format!")
  exit()
if FLAGS.output_encoder not in ['subword', 'token']:
  tf.logging.error("Unknown output encoder!")
  exit()


def linearise(root, begin_fn=lambda l: [], end_fn=lambda l: []):
  """Linearises a tree with integer sequences as labels."""
  if isinstance(root, LeafNode):
    return root.label
  lin = begin_fn(root.label)
  for c in root.children:
    lin.extend(linearise(c, begin_fn, end_fn))
  lin.extend(end_fn(root.label))
  return lin


def _int64_feature(value):
  return tf.train.Feature(int64_list=tf.train.Int64List(value=value))


class ExampleWriter(object):
  """Extracts examples and writes them to the output file."""

  def __init__(self):
    self.record_writer = tf.python_io.TFRecordWriter(FLAGS.output_filename)
    with open(FLAGS.vocab_filename) as f:
      self.idx_lookup = dict([(s.strip()[1:-1], idx) for idx, s in enumerate(f)
                              if s.startswith("'##")])
      tf.logging.info("Found %d non-terminal labels.", len(self.idx_lookup))
    self.nt_ids = {}
    if FLAGS.format in ["flat_nt_starttagged"]:
      self.nt_ids = {idx: True for idx in self.idx_lookup.itervalues()}
      self.nt_ids[text_encoder.EOS_ID] = True

  def maybe_delete_terminals(self, seq):
    """If nt_ids is not empty, delete all terminals in seq."""
    if not self.nt_ids:
      return seq
    return [t for t in seq if t in self.nt_ids]

  def write_examples(self, parse_tree):
    raise NotImplemented()

  def close(self):
    self.record_writer.close()

  def lookup_nt(self, pattern, key):
    """Reduces key to base name if necessary
    Throws various errors if key could not be found and/or conversion
    to base name failed.
    """
    try:
      return self.idx_lookup[pattern % key]
    except KeyError:
      split_chars = "-|="
      pos = [key.find(c) for c in split_chars]
      base_key_len = min([p for p in pos if p > 0])
      return self.idx_lookup[pattern % key[:base_key_len]]



class FlatExampleWriter(ExampleWriter): 

  def __init__(self):
    super(FlatExampleWriter, self).__init__()
    self.begin_fn = lambda l: [self.lookup_nt("##(%s##", l)]
    self.end_fn = lambda l: [self.lookup_nt("##%s)##", l)]
    if FLAGS.format in ["flat_starttagged", "flat_nt_starttagged"]:
      closing_bracket = self.idx_lookup["##)##"]
      self.end_fn = lambda l: [closing_bracket]
    elif FLAGS.format == "flat_endtagged":
      opening_bracket = self.idx_lookup["##(##"]
      self.begin_fn = lambda l: [opening_bracket]

  def write_examples(self, parse_tree, inputs):
    new_targets = linearise(parse_tree, self.begin_fn, self.end_fn)
    new_targets.append(text_encoder.EOS_ID)
    new_targets = self.maybe_delete_terminals(new_targets)
    example = tf.train.Example(features=tf.train.Features(feature={
      "inputs": _int64_feature(inputs),
      "targets": _int64_feature(new_targets)}))
    self.record_writer.write(example.SerializeToString())


class LayerByLayerExampleWriter(ExampleWriter): 

  def __init__(self):
    super(LayerByLayerExampleWriter, self).__init__()
    self.pop = []
    if FLAGS.format == "layerbylayer_pop":
      self.pop.append(self.idx_lookup["##POP##"])

  def write_examples(self, parse_tree, inputs):
    # We traverse in BFS order
    prev_nodes = [parse_tree]
    # TODO: We could avoid some lookups here
    while any(not n.is_leaf() for n in prev_nodes):
      next_nodes = []
      targets = []
      target_roots = []
      for root_node in prev_nodes:
        if root_node.is_leaf():
          target_roots.extend(root_node.label)
          for i in root_node.label:
            targets.extend([i] + self.pop)
          next_nodes.append(root_node)
        else:
          target_roots.append(self.lookup_nt("##%s##", root_node.label))
          for c in root_node.children:
            if c.is_leaf():
              targets.extend(c.label)
            else:
              targets.append(self.lookup_nt("##%s##", c.label))
          targets.extend(self.pop)
          next_nodes.extend(root_node.children)
      targets.append(text_encoder.EOS_ID)
      targets = self.maybe_delete_terminals(targets)
      target_roots.append(text_encoder.EOS_ID)
      example = tf.train.Example(features=tf.train.Features(feature={
        "inputs": _int64_feature(inputs), 
        "target_roots": _int64_feature(target_roots), 
        "targets": _int64_feature(targets)}))
      self.record_writer.write(example.SerializeToString())
      prev_nodes = next_nodes

  def _create_node_targets(self, node):
    if node.is_leaf():
      targets = []
    return []


class Node(object):
  """Represents a node in a parse tree."""

  def __init__(self, label):
    self.label = label
    self.children = []

  def __repr__(self):
    return "(%s %s %s)" % (self.label, self.children, self.label)

  def is_leaf(self):
    return False

  def get_plain_tokens(self):
    """Traverse DFS, get tokens without syntactic annotations."""
    return sum([c.get_plain_tokens() for c in self.children], [])

  def get_plain_str(self):
    """Traverse DFS, get tokens without syntactic annotations."""
    return sum([c.get_plain_str() for c in self.children], [])

  def encode_terminals(self, encoder, detokenizer):
    for c in self.children:
      c.encode_terminals(encoder, detokenizer)


class LeafNode(Node):
  """Represents a leaf node with a terminal label."""

  def __repr__(self):
    return str(self.label)

  def is_leaf(self):
    return True

  def get_plain_tokens(self):
    return self.label

  def get_plain_str(self):
    return [self.label]

  def encode_terminals(self, encoder, detokenizer):
    detok_label = detokenizer.detokenize(self.label)
    self.label = encoder.encode(detok_label)


def parse_penn(tokens):
  """Parses a string in penn treebank format into a tree data structure. tokens
  is the input string splitted at whitespace, `tokens` must not be empty.
  """
  root_nodes = []
  while tokens and tokens[0] != ")":
    if tokens[0][0] == "(": # tokens[0] is root label
      root = Node(tokens[0][1:])
      children, tokens = parse_penn(tokens[1:])
      root.children = children
      root_nodes.append(root)
    else:
      root_nodes.append(LeafNode(tokens[0]))
      tokens = tokens[1:]
  return root_nodes, tokens[1:]


def get_parse_trees():
  """Generator function, yields the root Node of the parse trees. """
  with open(FLAGS.penn_filename) as f:
    for line in f:
      tokens = line.strip().replace(")", " )").replace("( ", "(").split()
      root_nodes, rest_tokens = parse_penn(tokens)
      # Sanity checks
      if len(root_nodes) != 1 or rest_tokens:
        tf.logging.warning("Could not parse '%s'", line.strip())
      else:
        yield root_nodes[0]


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
  detokenizer = ptb_helper.SimpleDetokenizer()
  tf.logging.set_verbosity(tf.logging.INFO)
  if FLAGS.format.startswith("layerbylayer"):
    writer = LayerByLayerExampleWriter()
  else:
    writer = FlatExampleWriter()
  for parse_tree in get_parse_trees():
    if FLAGS.inputs_generator != "concat":
      str_tokens = parse_tree.get_plain_str()
      inputs = encoder.encode(" ".join(str_tokens))
    parse_tree.encode_terminals(encoder, detokenizer)
    if FLAGS.inputs_generator == "concat":
      inputs = parse_tree.get_plain_tokens()
    inputs.append(text_encoder.EOS_ID)
    writer.write_examples(parse_tree, inputs)
  writer.close()


if __name__ == "__main__":
  tf.app.run()
