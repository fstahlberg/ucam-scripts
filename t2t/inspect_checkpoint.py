# Copyright 2016 The TensorFlow Authors. All Rights Reserved.
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
# ==============================================================================
"""A simple script for inspect checkpoint files."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import sys

import numpy as np

from tensorflow.python import pywrap_tensorflow
from tensorflow.python.platform import app
from tensorflow.python.platform import flags

FLAGS = None


def print_tensors_in_checkpoint_file(file_name, tensor_name, print_content):
  try:
    reader = pywrap_tensorflow.NewCheckpointReader(file_name)
    var_to_shape_map = reader.get_variable_to_shape_map()
    for key in sorted(var_to_shape_map):
      if tensor_name in key:
        t = reader.get_tensor(key)
        print("%s: shape=%s abssum=%f" % (key, t.shape, np.sum(np.abs(t))))
        if print_content:
          print(reader.get_tensor(key))
          print("")
  except Exception as e:  # pylint: disable=broad-except
    print(str(e))
    if "corrupted compressed block contents" in str(e):
      print("It's likely that your checkpoint file has been compressed "
            "with SNAPPY.")
    if ("Data loss" in str(e) and
        (any([e in file_name for e in [".index", ".meta", ".data"]]))):
      proposed_file = ".".join(file_name.split(".")[0:-1])
      v2_file_error_template = """
It's likely that this is a V2 checkpoint and you need to provide the filename
*prefix*.  Try removing the '.' and extension.  Try:
inspect checkpoint --file_name = {}"""
      print(v2_file_error_template.format(proposed_file))


def main(unused_argv):
  if not FLAGS.file_name:
    print("Usage: inspect_checkpoint --file_name=checkpoint_file_name")
    sys.exit(1)
  else:
    print_tensors_in_checkpoint_file(FLAGS.file_name, FLAGS.tensor_name, FLAGS.print_content)


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.register("type", "bool", lambda v: v.lower() == "true")
  parser.add_argument(
      "--file_name",
      type=str,
      default="",
      help="Checkpoint filename. "
      "Note, if using Checkpoint V2 format, file_name is the "
      "shared prefix between all files in the checkpoint.")
  parser.add_argument(
      "--tensor_name",
      type=str,
      default="",
      help="Name of the tensor to inspect")
  parser.add_argument(
      "--print_content",
      nargs="?",
      const=True,
      type="bool",
      default=False,
      help="If True, print the values of all the tensors.")
  FLAGS, unparsed = parser.parse_known_args()
  app.run(main=main, argv=[sys.argv[0]] + unparsed)

