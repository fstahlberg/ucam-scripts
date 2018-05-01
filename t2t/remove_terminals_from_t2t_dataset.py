# coding=utf-8

r"""Removes the POP symbol from targets."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Dependency imports

import tensorflow as tf

tf.flags.DEFINE_integer("max_terminal_id", 30003,
                    "All target tokens less or equal this will be removed except EOS and PAD")
tf.flags.DEFINE_string("input_filename", "", "input filename")
tf.flags.DEFINE_string("output_filename", "", "output filename")
FLAGS = tf.flags.FLAGS


def _int64_feature(value):
  return tf.train.Feature(int64_list=tf.train.Int64List(value=value))


def main(_):
  tf.logging.set_verbosity(tf.logging.INFO)
  record_writer = tf.python_io.TFRecordWriter(FLAGS.output_filename)
  record_reader = tf.python_io.tf_record_iterator(FLAGS.input_filename)
  for record in record_reader:
    x = tf.train.Example()
    x.ParseFromString(record)
    tokens = [int(i) for i in x.features.feature["targets"].int64_list.value]
    example = tf.train.Example(features=tf.train.Features(feature={
      "inputs": x.features.feature["inputs"],
      "targets": _int64_feature([i for i in tokens if i < 2 or i > FLAGS.max_terminal_id])}))
    record_writer.write(example.SerializeToString())
  record_writer.close()


if __name__ == "__main__":
  tf.app.run()
