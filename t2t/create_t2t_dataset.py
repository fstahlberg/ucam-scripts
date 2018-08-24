# coding=utf-8
r"""Converts a plain text file to a T2T dataset with serialized examples."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Dependency imports

import tensorflow as tf

tf.flags.DEFINE_string("inputs_filename", "", "Plain text file with inputs")
tf.flags.DEFINE_string("targets_filename", "", "Plain text file with targets")
tf.flags.DEFINE_string("output_filename", "", "output filename")
tf.flags.DEFINE_bool("append_eos", False, "Add EOS")
FLAGS = tf.flags.FLAGS

EOS_ID = 1

def _int64_feature(line):
  value = [int(t) for t in line.strip().split()]
  if FLAGS.append_eos:
    value.append(EOS_ID)
  return tf.train.Feature(int64_list=tf.train.Int64List(value=value))


def main(_):
  tf.logging.set_verbosity(tf.logging.INFO)
  record_writer = tf.python_io.TFRecordWriter(FLAGS.output_filename)
  with open(FLAGS.inputs_filename) as inputs_handler:
    with open(FLAGS.targets_filename) as targets_handler:
      for inputs_line, targets_line in zip(inputs_handler, targets_handler): 
        example = tf.train.Example(features=tf.train.Features(feature={
          "inputs": _int64_feature(inputs_line),
          "targets": _int64_feature(targets_line)}))
        record_writer.write(example.SerializeToString())
  record_writer.close()


if __name__ == "__main__":
  tf.app.run()
