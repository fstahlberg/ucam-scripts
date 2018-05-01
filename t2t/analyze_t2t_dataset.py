# coding=utf-8
r"""Prints statistics about the number of tokens in a t2t data set.

ls ../tfnmt/t2t_data/translate_ende_wmt32k-train-* | python analyze_t2t_dataset.py --field targets
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Dependency imports

from tensor2tensor.data_generators import text_encoder
import sys
from collections import defaultdict

import tensorflow as tf

tf.flags.DEFINE_string("field", "targets",
                       "'inputs': Analyze input sequences\n"
                       "'targets': Analyze target sequences")
FLAGS = tf.flags.FLAGS

def main(_):
  """Convert a file to examples."""
  tf.logging.set_verbosity(tf.logging.INFO)
  counts = defaultdict(lambda: 0)
  total_sentences = 0
  for filename in sys.stdin:
    filename = filename.strip()
    reader = tf.python_io.tf_record_iterator(filename)
    n_sentences = 0
    for record in reader:
      x = tf.train.Example()
      x.ParseFromString(record)
      tokens = [int(i) for i in x.features.feature[FLAGS.field].int64_list.value]
      counts[len(tokens)] += 1
      n_sentences += 1
    tf.logging.info("Read %d sentences from %s.", n_sentences, filename)
    total_sentences += n_sentences

  tf.logging.info("Statistics for %s:", FLAGS.field)
  sorted_counts = [(l, f) for l, f in counts.iteritems()]
  sorted_counts.sort()
  acc = 0
  for l, f in sorted_counts:
    acc += f
    tf.logging.info("<=%d: %d/%d (%.3f%%)", l, acc, total_sentences, 100.0 * acc / total_sentences)

if __name__ == "__main__":
  tf.app.run()
