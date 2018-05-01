# coding=utf-8

r"""Removes the POP symbol from targets."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Dependency imports

import tensorflow as tf

tf.flags.DEFINE_string("vocab_filename", "",
                       "TokenTextEncoder or SubwordTextEncoder vocabulary file")
tf.flags.DEFINE_string("input_filename", "", "input filename")
tf.flags.DEFINE_string("output_filename", "", "output filename")
FLAGS = tf.flags.FLAGS


def _int64_feature(value):
  return tf.train.Feature(int64_list=tf.train.Int64List(value=value))


def main(_):
  tf.logging.set_verbosity(tf.logging.INFO)
  record_writer = tf.python_io.TFRecordWriter(FLAGS.output_filename)
  pop_idx = -1
  with open(FLAGS.vocab_filename) as f:
    for idx, s in enumerate(f):
      if s.strip() == "'##POP##'":
        pop_idx = idx
        break
  if pop_idx < 0:
    tf.logging.error("##POP## not found in vocabulary.")
    return
  tf.logging.info("##POP## token: %d" % pop_idx)
  record_reader = tf.python_io.tf_record_iterator(FLAGS.input_filename)
  for record in record_reader:
    x = tf.train.Example()
    x.ParseFromString(record)
    tokens = [int(i) for i in x.features.feature["targets"].int64_list.value]
    example = tf.train.Example(features=tf.train.Features(feature={
      "inputs": x.features.feature["inputs"],
      "target_roots": x.features.feature["target_roots"],
      "targets": _int64_feature([i for i in tokens if i != pop_idx])}))
    record_writer.write(example.SerializeToString())
  record_writer.close()


if __name__ == "__main__":
  tf.app.run()
