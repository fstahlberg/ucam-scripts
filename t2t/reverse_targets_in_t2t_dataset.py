# coding=utf-8
r"""Reverse target sequences in a T2T dataset."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Dependency imports

import tensorflow as tf

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
    if tokens[-1] != 1:
      sys.exit("Targets do not end with EOS!")
    example = tf.train.Example(features=tf.train.Features(feature={
      "inputs": x.features.feature["inputs"],
      "targets": _int64_feature(tokens[-2::-1] + [1])}))
    record_writer.write(example.SerializeToString())
  record_writer.close()


if __name__ == "__main__":
  tf.app.run()
