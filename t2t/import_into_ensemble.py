# coding=utf-8
# Adapted from t2t's avg_checkpoints
"""Script to import a single model into a t2t ensemble."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from collections import defaultdict

import os
import numpy as np
import six
from six.moves import zip  # pylint: disable=redefined-builtin
import tensorflow as tf

flags = tf.flags
FLAGS = flags.FLAGS

flags.DEFINE_string("ensemble_path", "",
                    "Path to the ensemble checkpoint.")
flags.DEFINE_integer("model_id", 0,
                     "ID of the imported model in the ensemble")
flags.DEFINE_string("model_path", "",
                    "Path to the model checkpoint.")
flags.DEFINE_string("model_name", "transformer",
                    "Model name.")
flags.DEFINE_string("output_path", "/tmp/averaged.ckpt",
                    "Path to output the new ensemble checkpoint with imported model to.")


def checkpoint_exists(path):
  return (tf.gfile.Exists(path) or tf.gfile.Exists(path + ".meta") or
          tf.gfile.Exists(path + ".index"))


def count_models(ensemble_var_list):
  models = {}
  for name, _ in ensemble_var_list:
    if name.startswith("ensemble/body/"):
      models[name.split("/")[2]] = True
  return len(models)


def main(_):
  print("READING MODEL CHECKPOINT FILE..................")
  body_var_values = {}
  embed_var_values = defaultdict(lambda: [])
  reader = tf.contrib.framework.load_checkpoint(FLAGS.model_path)
  model_var_list = tf.contrib.framework.list_variables(FLAGS.model_path)
  body_var_prefix = "%s/body/" % FLAGS.model_name
  for name, shape in model_var_list:
    tensor = reader.get_tensor(name)
    if name.startswith(body_var_prefix):
      name_in_ensemble = "ensemble/body/ens_model_%d/%s" % (FLAGS.model_id, name[len(body_var_prefix):])
      body_var_values[name_in_ensemble] = tensor
      print("Importing body var %s as %s" % (name, name_in_ensemble))
    if name.startswith("%s/symbol_modality" % FLAGS.model_name):
      parts = name.split("/")
      name_in_ensemble = "ensemble/%s/ens_weights_%d" % ("/".join(parts[1:-1]), FLAGS.model_id)
      shard_id = int(parts[-1].split("_")[-1])
      embed_var_values[name_in_ensemble].append((shard_id, tensor))
      print("Importing embed shard %s with ID %d into %s" % (name, shard_id, name_in_ensemble))

  print("READING ENSEMBLE CHECKPOINT FILE..................")
  var_values = {}
  var_dtypes = {}
  ensemble_var_list = tf.contrib.framework.list_variables(FLAGS.ensemble_path)
  n_models = count_models(ensemble_var_list)
  print("Ensemble consists of %d models" % n_models)
  for embed_name, tensors in embed_var_values.iteritems():
    print("Stacking %d tensors for embedding %s" % (len(tensors), embed_name))
    tensors.sort()
    embed_matrix = np.concatenate([t for _, t in tensors], axis=0)
    # Fix variable name (depends on number of models in the ensemble)
    parts = embed_name.split("/")
    mod_parts = parts[1].split("_")
    mod_parts[-1] = str(int(mod_parts[-1]) * 2)
    parts[1] = "_".join(mod_parts)
    embed_name_in_ensemble = "/".join(parts)
    body_var_values[embed_name_in_ensemble] = embed_matrix
  reader = tf.contrib.framework.load_checkpoint(FLAGS.ensemble_path)
  for name, shape in ensemble_var_list:
    tensor = reader.get_tensor(name)
    var_dtypes[name] = tensor.dtype
    if name in body_var_values:
      var_values[name] = body_var_values[name]
      print("Imported: %s" % name)
    elif name.startswith("training/ensemble/body/ens_model_%d" % FLAGS.model_id):
      var_values[name] = np.zeros(shape)
      print("To zero: %s" % name)
    else:
      var_values[name] = tensor
      print("Pass through: %s (abssum=%f)" % (name, np.sum(np.abs(tensor))))

  print("")
  print("WRITING ENSEMBLE CHECKPOINT FILE..................")
  tf_vars = [
      tf.get_variable(v, shape=var_values[v].shape, dtype=var_dtypes[v])
      for v in var_values
  ]
  placeholders = [tf.placeholder(v.dtype, shape=v.shape) for v in tf_vars]
  assign_ops = [tf.assign(v, p) for (v, p) in zip(tf_vars, placeholders)]
  saver = tf.train.Saver(tf.all_variables())

  with tf.Session() as sess:
    sess.run(tf.initialize_all_variables())
    for p, assign_op, (name, value) in zip(placeholders, assign_ops,
                                           six.iteritems(var_values)):
      sess.run(assign_op, {p: value})
    saver.save(sess, FLAGS.output_path)


if __name__ == "__main__":
  tf.app.run()
