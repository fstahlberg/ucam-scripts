# coding=utf-8
# Copyright 2017 The Tensor2Tensor Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

r"""NOTE: This is based on data_generators/inspect.py in the T2T
reporsitory, with the following differences:
- This one works.
- It does not print 'INPUTS:' and 'TARGETS:'
- It can also output integer sequences.

Below is the docstring of inspect.py

Inspect a TFRecord file of tensorflow.Example and show tokenizations.

python data_generators/inspect.py \
    --logtostderr \
    --print_targets \
    --subword_text_encoder_filename=$DATA_DIR/vocab.endefr.8192 \
    --input_filename=$DATA_DIR/wmt_ende_tokens_8k-train-00000-of-00100
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Dependency imports

from tensor2tensor.data_generators import text_encoder

import tensorflow as tf

tf.flags.DEFINE_string("output_encoder", "subword",
                       "'subword': SubwordTextEncoder\n"
                       "'token': TokenTextEncoder\n"
                       "'byte': ByteTextEncoder\n"
                       "'int': Output integers")
tf.flags.DEFINE_string("output_field", "targets",
                       "'inputs': Output input sequences\n"
                       "'targets': Output target sequences\n"
                       "'target_roots': Target side root sequences for "
                       "layer-by-layer models")
tf.flags.DEFINE_string("token_delimiter", "", "If set, use encoder to encode "
                       "each token separately.")
tf.flags.DEFINE_bool("silent", False, "Only print statistics")
tf.flags.DEFINE_bool("remove_eos", False, "Remove end-of-sentence markers")
tf.flags.DEFINE_string("vocab_filename", "",
                       "TokenTextEncoder or SubwordTextEncoder vocabulary file")
tf.flags.DEFINE_string("input_filename", "", "input filename")

FLAGS = tf.flags.FLAGS


class IntEncoder(object):
  def decode(self, tokens):
    return ' '.join([str(i) for i in tokens])

class OneByOneEncoderWrapper(object):
  def __init__(self, encoder, delimiter):
    self._encoder = encoder
    self._delimiter = delimiter

  def decode(self, tokens):
    return self._delimiter.join([self._encoder.decode([i]) for i in tokens])
  

def main(_):
  """Convert a file to examples."""
  tf.logging.set_verbosity(tf.logging.INFO)
  if FLAGS.output_encoder == "subword":
    encoder = text_encoder.SubwordTextEncoder(
        FLAGS.vocab_filename)
  elif FLAGS.output_encoder == "token":
    encoder = text_encoder.TokenTextEncoder(FLAGS.vocab_filename)
  elif FLAGS.output_encoder == "byte":
    encoder = text_encoder.ByteTextEncoder()
  elif FLAGS.output_encoder == "int":
    encoder = IntEncoder()
  else:
    tf.logging.error("Unknown encoder")
  if FLAGS.token_delimiter:
    encoder = OneByOneEncoderWrapper(encoder, FLAGS.token_delimiter)
  reader = tf.python_io.tf_record_iterator(FLAGS.input_filename)
  tf.logging.info("Encode %s with %s encoder.", FLAGS.input_filename, FLAGS.output_encoder)
  total_sequences = 0
  total_tokens = 0
  max_length = 0
  for record in reader:
    x = tf.train.Example()
    x.ParseFromString(record)
    tokens = [int(i) for i in x.features.feature[FLAGS.output_field].int64_list.value]
    if FLAGS.remove_eos and tokens and tokens[-1] == text_encoder.EOS_ID:
      tokens = tokens[:-1]
    if not FLAGS.silent:
      print(encoder.decode(tokens))
    total_tokens += len(tokens)
    total_sequences += 1
    max_length = max(max_length, len(tokens))

  tf.logging.info("total_sequences: %d", total_sequences)
  tf.logging.info("total_tokens: %d", total_tokens)
  tf.logging.info("max_length: %d", max_length)


if __name__ == "__main__":
  tf.app.run()
