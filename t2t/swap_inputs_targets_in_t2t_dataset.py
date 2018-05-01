# coding=utf-8
r"""Swaps targets and inputs in a T2T dataset."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Dependency imports

import tensorflow as tf

tf.flags.DEFINE_string("input_filename", "", "input filename")
tf.flags.DEFINE_string("output_filename", "", "output filename")
FLAGS = tf.flags.FLAGS

def main(_):
  tf.logging.set_verbosity(tf.logging.INFO)
  record_writer = tf.python_io.TFRecordWriter(FLAGS.output_filename)
  record_reader = tf.python_io.tf_record_iterator(FLAGS.input_filename)
  for record in record_reader:
    x = tf.train.Example()
    x.ParseFromString(record)
    example = tf.train.Example(features=tf.train.Features(feature={
      "inputs": x.features.feature["targets"],
      "targets": x.features.feature["inputs"]}))
    record_writer.write(example.SerializeToString())
  record_writer.close()


if __name__ == "__main__":
  tf.app.run()
