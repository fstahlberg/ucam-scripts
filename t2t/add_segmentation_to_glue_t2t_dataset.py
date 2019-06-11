# coding=utf-8
r"""Add inputs_seg, inputs_pos and targets_seg, targets_pos to T2T dataset."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Dependency imports

import tensorflow as tf

tf.flags.DEFINE_string("input_filename", "", "input filename")
tf.flags.DEFINE_string("output_filename", "", "output filename")
FLAGS = tf.flags.FLAGS

EOS_ID = 1
GO_ID = 2

def _int64_feature(value):
  return tf.train.Feature(int64_list=tf.train.Int64List(value=value))

def main(_):
  tf.logging.set_verbosity(tf.logging.INFO)
  record_writer = tf.python_io.TFRecordWriter(FLAGS.output_filename)
  record_reader = tf.python_io.tf_record_iterator(FLAGS.input_filename)
  for record in record_reader:
    x = tf.train.Example()
    x.ParseFromString(record)
    out_features = {}
    for field in x.features.feature:
      feature = x.features.feature[field]
      out_features[field] = feature
      tokens = [int(i) for i in feature.int64_list.value]
      seg = [0] * len(tokens)
      pos = [0] * len(tokens)
      seg_id = 1
      tok_id = 0
      for idx, tok in enumerate(tokens):
        seg[idx] = seg_id
        pos[idx] = tok_id
        if tok == GO_ID:
          seg_id += 1
          tok_id = 0
        else:
          tok_id += 1
      out_features["%s_seg" % field] = _int64_feature(seg)
      out_features["%s_pos" % field] = _int64_feature(pos)
    example = tf.train.Example(features=tf.train.Features(feature=out_features))
    record_writer.write(example.SerializeToString())
  record_writer.close()


if __name__ == "__main__":
  tf.app.run()
