# coding=utf-8

r"""This script creates T2T datasets for layer-by-layer models or other
target side syntax based models. The parse trees are loaded from a plain
text file. The script can deal with skipped sentences for which the 
parser failed to find any derivation, for example because they are 
ill-formated, empty, or too long.

The new dataset follows the tokenization in the source dataset. The
parse trees are assumed to be on the word level with PTB tokenization
as produced by the stanford parser.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Dependency imports
import re

from tensor2tensor.data_generators import text_encoder

import tensorflow as tf

tf.flags.DEFINE_string("output_encoder", "subword",
                       "'subword': SubwordTextEncoder\n"
                       "'token': TokenTextEncoder")
tf.flags.DEFINE_string("vocab_filename", "",
                       "TokenTextEncoder or SubwordTextEncoder vocabulary file")
tf.flags.DEFINE_string("input_filename", "", "input filename")
tf.flags.DEFINE_string("output_filename", "", "output filename")
tf.flags.DEFINE_string("penn_filename", "", "Parse trees, one each line. For "
                       "example the .penn.compact file from lexparser_std.sh")
tf.flags.DEFINE_string("format", "layerbylayer_pop", "This parameter controls "
                       "how the parse trees are integrated in the TFRecord.\n"
                       " 'layerbylayer': For layer-by-layer models.\n"
                       " 'layerbylayer_pop': layer-by-layer with POP control "
                       " symbols for monotone attention on previous layer.\n"
                       " 'flat_starttagged': Linearised tree, '(' tagged.\n"
                       " 'flat_endtagged': Linearised tree, ')' tagged.\n"
                       " 'flat_bothtagged': Linearised tree, '(' and ')' tagged.\n")

FLAGS = tf.flags.FLAGS

# Sanity checks
if FLAGS.format not in ['layerbylayer', 'layerbylayer_pop', 'flat_starttagged', 
                        'flat_endtagged', 'flat_bothtagged']:
  tf.logging.error("Unknown format!")
  exit()
if FLAGS.output_encoder not in ['subword', 'token']:
  tf.logging.error("Unknown output encoder!")
  exit()

penn_disambiguate_map = [
  ("(", "-LRB-"), 
  (")", "-RRB-"), 
  ("[", "-LSB-"), 
  ("]", "-RSB-"), 
  ("{", "-LCB-"), 
  ("}", "-RCB-"),
  ("&amp;", "&"),
  ("–", "--"),
  ("—", "--"),
  ("\xc2\xad", "-"),
  ("\"", "''"),
  ("\"", "``"),
  ("'", "`"),
  ("“", "``"),
  ("”", "''"),
  ("‘", "`"),
  ("’", "'"),
  ("«", "``"),
  ("»", "''"),
  ("‹", "`"),
  ("›", "'"),
  ("„", "``"),
  ("”", "''"),
  ("‚", "`"),
  ("’", "'"),
  ("€", "$"),
  ("\u00A2", "$"),
  ("\u00A3", "$"),
  ("\u00A4", "$"),
  ("\u00A5", "$"),
  ("\u0080", "$"),
  ("\u20A0", "$"),
  ("\u20AA", "$"),
  ("\u20AC", "$"),
  ("\u20B9", "$"),
  ("\u060B", "$"),
  ("\u0E3F", "$"),
  ("\u20A4", "$"),
  ("\uFFE0", "$"),
  ("\uFFE1", "$"),
  ("\uFFE5", "$"),
  ("\uFFE6", "$")
]

def escape_ambiguous_chars(s):
  for unescaped, escaped in penn_disambiguate_map:
    s = s.replace(unescaped, escaped)
  #print("ESCAPED: '%s'" % s)
  return s


def is_similar(record_idx, s1, s2):
  s1_ascii = ''.join([i for i in s1 if ord(i) < 128])
  s2_ascii = ''.join([i for i in s2 if ord(i) < 128])
  similar = False
  warn_msg = "Record %d: Skip record (%d != %d). " \
             "\nRecordStr: '%s'\nParseStr:  '%s'\nDist: %f\nDistAscii: %f"
  l = float(max(len(s1), len(s2)))
  lev = float(levenshtein(s1, s2)) / l
  lev_ascii = float(levenshtein(s1_ascii, s2_ascii)) / l
  if lev <= 0.35:
    warn_msg = "Record %d: Slight mismatch between record string and " \
               "parse string length (%d != %d). We think this is a " \
               "tokenization issue, and skip the record and parse tree." \
               "\nRecordStrLev: '%s'\nParseStrLev:  '%s'\nDist: %f\n" \
               "DistAscii: %f"
    similar = True
  if lev_ascii <= 0.1 and l >= 6:
    warn_msg = "Record %d: Slight mismatch between record string and " \
               "parse string length (%d != %d). We think this is a " \
               "tokenization issue, and skip the record and parse tree." \
               "\nRecordStrLevAscii: '%s'\nParseStrLevAscii:  '%s'\nDist: %f" \
               "DistAscii: %f"
    similar = True
  tf.logging.warning(
    warn_msg, record_idx, len(s1), len(s2), s1, s2, lev, lev_ascii)
  return similar


# https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance#Python
def levenshtein(s1, s2):
  if len(s1) < len(s2):
    return levenshtein(s2, s1)
  # len(s1) >= len(s2)
  if len(s2) == 0:
    return len(s1)
  previous_row = range(len(s2) + 1)
  for i, c1 in enumerate(s1):
    current_row = [i + 1]
    for j, c2 in enumerate(s2):
      insertions = previous_row[j + 1] + 1
      deletions = current_row[j] + 1
      substitutions = previous_row[j] + (c1 != c2)
      current_row.append(min(insertions, deletions, substitutions))
    previous_row = current_row
  return previous_row[-1]


def linearise(root, begin_fn=lambda l: [], end_fn=lambda l: []):
  """Linearises a tree with integer sequences as labels."""
  if not root.children:
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

  def write_examples(self, src_example, parse_tree):
    raise NotImplemented()

  def close(self):
    self.record_writer.close()


class FlatExampleWriter(ExampleWriter): 

  def __init__(self):
    super(FlatExampleWriter, self).__init__()
    self.begin_fn = lambda l: [self.idx_lookup["##(%s##" % l]]
    self.end_fn = lambda l: [self.idx_lookup["##%s)##" % l]]
    if FLAGS.format == "flat_starttagged":
      closing_bracket = self.idx_lookup["##)##"]
      self.end_fn = lambda l: [closing_bracket]
    elif FLAGS.format == "flat_endtagged":
      opening_bracket = self.idx_lookup["##(##"]
      self.begin_fn = lambda l: [opening_bracket]

  def write_examples(self, src_example, parse_tree):
    new_targets = linearise(parse_tree, self.begin_fn, self.end_fn)
    new_targets.append(text_encoder.EOS_ID)
    example = tf.train.Example(features=tf.train.Features(feature={
      "inputs": src_example.features.feature["inputs"],
      "targets": _int64_feature(new_targets)}))
    self.record_writer.write(example.SerializeToString())


class LayerByLayerExampleWriter(ExampleWriter): 

  def __init__(self):
    super(LayerByLayerExampleWriter, self).__init__()
    self.pop = []
    if FLAGS.format == "layerbylayer_pop":
      self.pop.append(self.idx_lookup["##POP##"])

  def write_examples(self, src_example, parse_tree):
    # We traverse in BFS order
    inputs = src_example.features.feature["inputs"]
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
          target_roots.append(self.idx_lookup["##%s##" % root_node.label])
          for c in root_node.children:
            if c.is_leaf():
              targets.extend(c.label)
            else:
              targets.append(self.idx_lookup["##%s##" % c.label])
          targets.extend(self.pop)
          next_nodes.extend(root_node.children)
      targets.append(text_encoder.EOS_ID)
      target_roots.append(text_encoder.EOS_ID)
      example = tf.train.Example(features=tf.train.Features(feature={
        "inputs": inputs,
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

  def get_plain_str(self):
    return "".join([c.get_plain_str() for c in self.children])

  def get_str_length(self):
    """Counts the length of the string covered by this node. We do
    not count whitespace.
    """
    return sum([c.get_str_length() for c in self.children])

  def encode_terminals(self, tokens, token_lengths):
    """Replaces labels in all leaf nodes under this node with integer
    sequences. The integers are taken from `tokens`. This method works
    under the assumption that the prefix of `tokens` encodes the
    terminals in this subtree up to blank symbols.

    Returns:
      Suffix of `tokens` which has not been used.
    """
    for c in self.children:
      tokens, token_lengths = c.encode_terminals(tokens, token_lengths)
    return tokens, token_lengths

  def disambiguate_escaped_chars(self, ref_str):
    """The PTB tokenization of the long hyphen '–' is problematic:
    Both '–' and '--' are normalized to '--'. This method traverses
    the subtree and replaces all '--' in the tree with '–' or '--',
    depending on the character in `ref_str` at the corresponding position
    """
    for c in self.children:
      ref_str = c.disambiguate_escaped_chars(ref_str)
    return ref_str

  def remove_empty_nodes(self):
    """Removes empty nodes in the subtree recursively.

    Returns false if this node is empty after clearing the subtree, 
    and true otherwise.
    """
    self.children = [c for c in self.children if c.remove_empty_nodes()]
    if not self.children:
      return False
    return True


class LeafNode(Node):
  """Represents a leaf node with a terminal label."""

  def __repr__(self):
    return str(self.label)

  def is_leaf(self):
    return True

  def get_plain_str(self):
    return str(self.label)

  def get_str_length(self):
    #print("'%s': %d" % (self.label, len_no_blank(self.label)))
    return len_no_blank(self.label)

  def encode_terminals(self, tokens, token_lengths):
    if not tokens: # tokens are empty -> create empty leaf
      self.label = []
      return [], []
    my_length = self.get_str_length()
    my_tokens = []
    while my_length > 0:
      my_length -= token_lengths.pop(0)
      my_tokens.append(tokens.pop(0))
    while token_lengths and token_lengths[0] == 0:
      token_lengths.pop(0)
      my_tokens.append(tokens.pop(0))
    if token_lengths and my_length < 0:
      token_lengths[0] -= my_length
    self.label = my_tokens
    #print("my tokens (len %d): %s" %(my_length, my_tokens))
    #print("tokens: %s" % tokens)
    #print("token_length: %s" % token_lengths)
    return tokens, token_lengths

  def disambiguate_escaped_chars(self, ref_str):
    for unescaped, escaped in penn_disambiguate_map:
      if ref_str.startswith(unescaped) and self.label == escaped:
        self.label = unescaped
    return ref_str[len_no_blank(self.label):]

  def remove_empty_nodes(self):
    if not self.label:
      return False
    return True


def no_blank(s):
  return re.sub(r"\s+", "", s.replace("\xc2\xa0", ""), flags=re.UNICODE)


def len_no_blank(s):
  return len(no_blank(s))
  #return len(s) - s.count(" ")


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
  """Generator function, yields pairs (tree, length), where tree
  is the root Node of the parse tree, and length is the number of
  terminal symbols, ie. the string length without syntactic annotations
  and without whitespace.
  """
  with open(FLAGS.penn_filename) as f:
    for line in f:
      tokens = line.strip().replace(")", " )").split()
      root_nodes, rest_tokens = parse_penn(tokens)
      # Sanity checks
      if len(root_nodes) != 1 or rest_tokens:
        tf.logging.warning("Could not parse '%s'", line.strip())
      else:
        yield root_nodes[0], root_nodes[0].get_str_length()


def main(_):
  """Convert a file to examples."""
  tf.logging.set_verbosity(tf.logging.INFO)
  if FLAGS.output_encoder == "subword":
    encoder = text_encoder.SubwordTextEncoder(
        FLAGS.vocab_filename)
  elif FLAGS.output_encoder == "token":
    encoder = text_encoder.TokenTextEncoder(FLAGS.vocab_filename)
  else:
    tf.logging.error("Unknown encoder")

  # Load parse trees
  tf.logging.info("Loading parse trees...")
  trees = []

  # Read records
  tf.logging.info("Walk through records...")
  record_reader = tf.python_io.tf_record_iterator(FLAGS.input_filename)
  parse_tree_reader = get_parse_trees()
  parse_tree, parse_str_length = next(parse_tree_reader)
  if FLAGS.format.startswith("layerbylayer"):
    writer = LayerByLayerExampleWriter()
  else:
    writer = FlatExampleWriter()
  try:
    for record_idx, record in enumerate(record_reader):
      x = tf.train.Example()
      x.ParseFromString(record)
      tokens = [int(i) for i in x.features.feature["targets"].int64_list.value]
      print(tokens)
      if tokens and tokens[-1] == text_encoder.EOS_ID:
        tokens = tokens[:-1]
      else:
        tf.logging.warning("Target sequence without EOS!")
      record_str = encoder.decode(tokens)
      if ("&nbsp;" in record_str) or ("........" in record_str):
        tf.logging.warning("Skip because of &nbsp; or ........")
        parse_tree, parse_str_length = next(parse_tree_reader)
      record_str_no_blank = no_blank(escape_ambiguous_chars(record_str))
      if len(record_str_no_blank) == parse_str_length:
        parse_tree.disambiguate_escaped_chars(record_str.replace(" ", ""))
        token_lengths = [len_no_blank(encoder.decode([i])) for i in tokens]
        try:
          t1, t2 = parse_tree.encode_terminals(list(tokens), token_lengths)
        except IndexError:
          t1 = -1 # Trigger warning
        if t1 or t2:
          tf.logging.warning("Could not tokenize tree for '%s'.\n"
                             "Tokens: %s\nRest tokens: %s", 
                             record_str,
                             [encoder.decode([i]) for i in tokens],
                             t1)
        else:
          parse_tree.remove_empty_nodes() # encode_terminals can produce some.
          writer.write_examples(x, parse_tree)
        parse_tree, parse_str_length = next(parse_tree_reader)
      else:
        parse_plain_str = parse_tree.get_plain_str()
        if is_similar(record_idx, record_str_no_blank, parse_plain_str):
          parse_tree, parse_str_length = next(parse_tree_reader)
  except StopIteration:
    tf.logging.warning("Not enough parse trees! Discarding remaining records")
  writer.close()


if __name__ == "__main__":
  tf.app.run()
