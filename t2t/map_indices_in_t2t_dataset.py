# coding=utf-8
r"""Maps the indices in a t2t dataset for another vocabulary file.
Skips tokens which are not in the new vocabulary.
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
  mapped = [id_map[i] for i in tokens if i in id_map]
  return tf.train.Feature(int64_list=tf.train.Int64List(value=mapped))


def main(_):
  tf.logging.set_verbosity(tf.logging.INFO)
  record_writer = tf.python_io.TFRecordWriter(FLAGS.output_filename)
  record_reader = tf.python_io.tf_record_iterator(FLAGS.input_filename)
  id_map = {}
  with open(FLAGS.old_vocab_filename) as f:
      old_str2id = dict([(s, idx) for idx, s in enumerate(f)])
  with open(FLAGS.new_vocab_filename) as f:
    for idx, s in enumerate(f):
      if s in old_str2id:
        id_map[old_str2id[s]] = idx
  tf.logging.info("ID map contains %d entries" % len(id_map))
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
