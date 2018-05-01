#!/usr/bin/env python
# coding=utf-8
# Copyright 2017 The Tensor2Tensor Authors and Cambridge University.
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

r"""Apply T2T preprocessing.

This binary converts between raw text and the internal representation of
sentences as sequences of integers. This script is similar to the apply_wmap.py
script but performs tokenization or detokenization before applying the word map.
Use this script to make sure that components which are combined with 
tensor2tensor use the same vocabulary and preprocessing approach as 
tensor2tensor.

Example usage:

  apply_t2t_preprocessing.py \
      --dir i2s --vocab_filename=t2t_data/vocab.endefr \
      < sentences_indexed.txt > sentences_raw.txt 

Note that EOS is not expected to be in the input, and is not appended to the
output.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sys

# Dependency imports

from tensor2tensor.data_generators import text_encoder

import tensorflow as tf

flags = tf.flags
FLAGS = flags.FLAGS

flags.DEFINE_string("dir", "i2s",
                    "s2i: Convert from raw text to integers. i2s: Convert "
                    "from integers to raw text.")
tf.flags.DEFINE_string("output_encoder", "subword",
                       "'subword': SubwordTextEncoder\n"
                       "'token': TokenTextEncoder\n"
                       "'byte': ByteTextEncoder")
tf.flags.DEFINE_string("output_field", "targets",
                       "'inputs': Output input sequences\n"
                       "'targets': Output target sequences\n"
                       "'target_roots': Target side root sequences for "
                       "layer-by-layer models")
tf.flags.DEFINE_string("token_delimiter", "", "If set, use encoder to encode "
                       "each token separately.")
tf.flags.DEFINE_string("vocab_filename", "",
                       "TokenTextEncoder or SubwordTextEncoder vocabulary file")
tf.flags.DEFINE_bool("handle_bos_eos", False, "Treat <s> and </s> separately."
                     "Only applicable to s2i direction.")

BOS_ID = 2
EOS_ID = 1
BOS_STR = "<s>"
EOS_STR = "</s>"
BOS_LEN = len(BOS_STR)
EOS_LEN = len(EOS_STR)

class OneByOneEncoderWrapper(object):
  def __init__(self, encoder, delimiter):
    self._encoder = encoder
    self._delimiter = delimiter

  def decode(self, tokens):
    return self._delimiter.join([self._encoder.decode([i]) for i in tokens])


def main(_):
  if FLAGS.output_encoder == "subword":
    encoder = text_encoder.SubwordTextEncoder(
        FLAGS.vocab_filename)
  elif FLAGS.output_encoder == "token":
    encoder = text_encoder.TokenTextEncoder(FLAGS.vocab_filename)
  elif FLAGS.output_encoder == "byte":
    encoder = text_encoder.ByteTextEncoder()
  else:
    tf.logging.error("Unknown encoder")
  if FLAGS.token_delimiter:
    encoder = OneByOneEncoderWrapper(encoder, FLAGS.token_delimiter)
  encode = FLAGS.dir == "s2i"
  for line in sys.stdin:
    line = line.strip()
    if encode:
      if FLAGS.handle_bos_eos:
        has_bos = False
        has_eos = False
        if line[:BOS_LEN] == BOS_STR:
          has_bos = True
          line = line[BOS_LEN:]
        if line[-EOS_LEN:] == EOS_STR:
          has_eos = True
          line = line[:-EOS_LEN]
        tokens = encoder.encode(line)
        if has_bos:
          tokens = [BOS_ID] + tokens
        if has_eos:
          tokens.append(EOS_ID)
        print(" ".join(map(str, tokens)))
      else:
        print(" ".join([str(i) for i in encoder.encode(line)]))
    else:
      print(encoder.decode([int(s) for s in line.split()]))


if __name__ == "__main__":
  tf.app.run()
