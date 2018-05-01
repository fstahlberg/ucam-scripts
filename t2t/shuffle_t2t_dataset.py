# coding=utf-8
r"""Shuffles the records in a T2T dataset file."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
from random import shuffle

tf.flags.DEFINE_string("input_filename", "", "input filename")
tf.flags.DEFINE_string("output_filename", "", "output filename")

FLAGS = tf.flags.FLAGS


def main(_):
  tf.logging.set_verbosity(tf.logging.INFO)
  reader = tf.python_io.tf_record_iterator(FLAGS.input_filename)
  writer = tf.python_io.TFRecordWriter(FLAGS.output_filename)
  tf.logging.info("Reading records from %s..." % FLAGS.input_filename)
  records = [record for record in reader]
  tf.logging.info("Shuffling %d records..." % len(records))
  shuffle(records)
  tf.logging.info("Writing records...")
  for record in records:
    writer.write(record)
  writer.close()


if __name__ == "__main__":
  tf.app.run()
