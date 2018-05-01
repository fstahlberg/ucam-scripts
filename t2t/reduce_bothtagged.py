# coding=utf-8
r"""Converts flat_bothtagged format to flat_starttagged
or flat_endtagged.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Dependency imports

import tensorflow as tf

tf.flags.DEFINE_string("input_filename", "", "input filename")
tf.flags.DEFINE_string("output_filename", "", "output filename")
tf.flags.DEFINE_string("old_vocab_filename", "", "Vocabulary file for input")
tf.flags.DEFINE_string("new_vocab_filename", "", "Vocabulary file for output")
tf.flags.DEFINE_string("field", "targets", "inputs, targets (feature to map)")
FLAGS = tf.flags.FLAGS


def map_tokens(feat, id_map):
  tokens = [int(i) for i in feat.int64_list.value]
  mapped = [id_map.get(i, i) for i in tokens]
  return tf.train.Feature(int64_list=tf.train.Int64List(value=mapped))


def main(_):
  tf.logging.set_verbosity(tf.logging.INFO)
  record_writer = tf.python_io.TFRecordWriter(FLAGS.output_filename)
  record_reader = tf.python_io.tf_record_iterator(FLAGS.input_filename)
  old_opening = []
  old_closing = []
  old_str2id = {}
  with open(FLAGS.old_vocab_filename) as f:
    for idx, s in enumerate(f):
      s = s.strip()
      old_str2id[s] = idx
      if s[:4] == "'##(":
        old_opening.append(idx)
      if s[-4:] == ")##'":
        old_closing.append(idx)
  new_opening = None
  new_closing = None
  id_map = {}
  with open(FLAGS.new_vocab_filename) as f:
    for idx, s in enumerate(f):
      s = s.strip()
      if s in old_str2id:
        id_map[old_str2id[s]] = idx
      if s == "'##(##'":
        new_opening = idx
      elif s == "'##)##'":
        new_closing = idx
  if new_opening is not None:
    mapping = {idx: new_opening for idx in old_opening}
    tf.logging.info("Map %d opening brackets to ID %d" % (len(mapping), new_opening))
    id_map.update(mapping)
  if new_closing is not None:
    mapping = {idx: new_closing for idx in old_closing}
    tf.logging.info("Map %d closing brackets to ID %d" % (len(mapping), new_closing))
    id_map.update(mapping)
  for record in record_reader:
    x = tf.train.Example()
    x.ParseFromString(record)
    mapped_feats = {}
    for field, feat in x.features.feature.iteritems():
      if field in FLAGS.field:
        mapped_feats[field] = map_tokens(feat, id_map)
      else:
        mapped_feats[field] = feat
    example = tf.train.Example(features=tf.train.Features(feature=mapped_feats))
    record_writer.write(example.SerializeToString())
  record_writer.close()


if __name__ == "__main__":
  tf.app.run()
