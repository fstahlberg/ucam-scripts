# coding=utf-8
r"""Moses n-best list rescoring.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import operator
import numpy as np


from tensor2tensor import models  # pylint: disable=unused-import
from tensor2tensor import problems as problems_lib  # pylint: disable=unused-import
from tensor2tensor.utils import usr_dir
from tensor2tensor.utils import registry
from tensor2tensor.utils import devices
from tensor2tensor.utils import trainer_lib
from tensor2tensor.data_generators.text_encoder import TextEncoder
from tensor2tensor.data_generators import problem  # pylint: disable=unused-import
from tensor2tensor.data_generators import text_encoder
from tensorflow.python.training import saver
from tensorflow.python.training import training

import tensorflow as tf

flags = tf.flags
FLAGS = flags.FLAGS

flags.DEFINE_string("src_test", None, "Path to source sentences.")
flags.DEFINE_string("trg_test", None, "Path to target n-best list.")
flags.DEFINE_string("checkpoint_path", None,
                    "Path to the model checkpoint.")
flags.DEFINE_bool("single_cpu_thread", False,
                  "If true, do not use more than one CPU")
flags.DEFINE_string("t2t_usr_dir", None, "Path to the t2t usr directory.")
flags.DEFINE_string("problem", None, "T2T problem name.")
flags.DEFINE_string("model", None, "T2T model name.")
flags.DEFINE_string("hparams_set", None, "T2T hparams set name.")
flags.DEFINE_string("outputs", "text,nbest", "Output formats (like in SGNMT).")
flags.DEFINE_string("output_path", "t2t-gibbs-out.%s", "Output path (like in SGNMT).")

EOS_ID = 1
PAD_ID = 0


class DummyTextEncoder(TextEncoder):
  """Dummy TextEncoder implementation. The TextEncoder 
  implementation in tensor2tensor reads the vocabulary file in
  the constructor, which is not available inside SGNMT. This
  class can be used to replace the standard TextEncoder 
  implementation with a fixed vocabulary size. Note that this
  encoder cannot be used to translate between raw text and
  integer sequences.
  """

  def __init__(self, vocab_size):
    super(DummyTextEncoder, self).__init__(num_reserved_ids=None)
    self._vocab_size = vocab_size

  def encode(self, s):
    raise NotImplementedError("Dummy encoder cannot be used to encode.")

  def decode(self, ids):
    raise NotImplementedError("Dummy encoder cannot be used to decode.")

  @property
  def vocab_size(self):
    return self._vocab_size


def session_config():
  """Creates the session config with t2t default parameters."""
  graph_options = tf.GraphOptions(optimizer_options=tf.OptimizerOptions(
    opt_level=tf.OptimizerOptions.L1, do_function_inlining=False))
  if FLAGS.single_cpu_thread:
    config = tf.ConfigProto(
        intra_op_parallelism_threads=1,
        inter_op_parallelism_threads=1,
        allow_soft_placement=True,
        graph_options=graph_options,
        log_device_placement=False)
  else:
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.95)
    config = tf.ConfigProto(
        allow_soft_placement=True,
        graph_options=graph_options,
        gpu_options=gpu_options,
        log_device_placement=False)
  return config


def create_session():
  """Creates a MonitoredSession for this predictor."""
  if not FLAGS.checkpoint_path:
    raise AttributeError("Please set --checkpoint_path")
  try:
    if os.path.isdir(FLAGS.checkpoint_path):
      checkpoint_path = saver.latest_checkpoint(FLAGS.checkpoint_path)
    else:
       checkpoint_path = FLAGS.checkpoint_path
       tf.logging.info("%s is not a directory. Interpreting as direct "
                    "path to checkpoint..." % checkpoint_path)
    return training.MonitoredSession(
        session_creator=training.ChiefSessionCreator(
        checkpoint_filename_with_path=checkpoint_path,
        config=session_config()))
  except tf.errors.NotFoundError as e:
    tf.logging.fatal("Could not find all variables of the computation "
                  "graph in the T2T checkpoint file. This means that the "
                  "checkpoint does not correspond to the specified model")
    raise AttributeError("Could not initialize TF session.")


def log_prob_from_logits(logits):
  """Softmax function."""
  return logits - tf.reduce_logsumexp(logits, axis=-1, keepdims=True)


def expand_input_dims_for_t2t(t):
  """Expands a plain input tensor for using it in a T2T graph.
  Args:
      t: Tensor
  Returns:
    Tensor `t` expanded by two dimensions on the right.
  """
  t = tf.expand_dims(t, -1) # Because of modality
  t = tf.expand_dims(t, -1) # Because of random reason X
  return t


def gather_2d(params, indices):
  """This is a batched version of tf.gather(), ie. it applies tf.gather() to
  each batch separately.

  Example:
    params = [[10, 11, 12, 13, 14],
              [20, 21, 22, 23, 24]]
    indices = [[0, 0, 1, 1, 1, 2],
               [1, 3, 0, 0, 2, 2]]
    result = [[10, 10, 11, 11, 11, 12],
              [21, 23, 20, 20, 22, 22]]

  Args:
    params: A [batch_size, n, ...] tensor with data
    indices: A [batch_size, num_indices] int32 tensor with indices into params.
             Entries must be smaller than n

  Returns:
    The result of tf.gather() on each entry of the batch.
  """
  # TODO(fstahlberg): Curse TF for making this so awkward.
  batch_size = tf.shape(params)[0]
  num_indices = tf.shape(indices)[1]
  batch_indices = tf.tile(tf.expand_dims(tf.range(batch_size), 1),
                          [1, num_indices])
  # batch_indices is [[0,0,0,0,...],[1,1,1,1,...],...]
  gather_nd_indices = tf.stack([batch_indices, indices], axis=2)
  return tf.gather_nd(params, gather_nd_indices)


class Rescorer(object):

  def __init__(self):
    rescoring_graph = tf.Graph()
    with rescoring_graph.as_default() as g:
      hparams = trainer_lib.create_hparams(FLAGS.hparams_set)
      self._add_problem_hparams(hparams)
      translate_model = registry.model(FLAGS.model)(
          hparams, tf.estimator.ModeKeys.EVAL)
      self._inputs_var = tf.placeholder(dtype=tf.int32, shape=[FLAGS.batch_size, None],
                                        name="rescorer_inputs")
      self._targets_var = tf.placeholder(dtype=tf.int32, shape=[FLAGS.batch_size, None], 
                                         name="rescorer_targets")
      features = {"inputs": expand_input_dims_for_t2t(self._inputs_var), 
                  "targets": expand_input_dims_for_t2t(self._targets_var)}
      translate_model.prepare_features_for_infer(features)
      translate_model._fill_problem_hparams_features(features)
      logits, _ = translate_model(features)
      logits = tf.squeeze(logits, [2, 3])
      log_probs = log_prob_from_logits(logits)
      no_pad = tf.cast(tf.not_equal(self._targets_var, PAD_ID), tf.float32)
      shp = tf.shape(self._targets_var)
      flat_bsz = shp[0] * shp[1]
      word_loss = gather_2d(
          tf.reshape(log_probs, [flat_bsz, -1]),
          tf.reshape(self._targets_var, [flat_bsz, 1]))
      word_loss = tf.reshape(word_loss, (shp[0], shp[1])) * no_pad
      self._sentence_loss = tf.reduce_sum(word_loss, -1)
      self.mon_sess = create_session()

  def _add_problem_hparams(self, hparams):
    """Add problem hparams for the problems. 
    This method corresponds to create_hparams() in tensor2tensor's
    trainer_lib module, but replaces the feature encoders with
    DummyFeatureEncoder's.
    Args:
        hparams (Hparams): Model hyper parameters.
      
    Returns:
        hparams object.
    Raises:
        LookupError if the problem name is not in the registry or
        uses the old style problem_hparams.
    """
    problem = registry.problem(FLAGS.problem)
    problem._encoders = {
        "inputs": DummyTextEncoder(vocab_size=FLAGS.src_vocab_size),
        "targets": DummyTextEncoder(vocab_size=FLAGS.trg_vocab_size)
    }
    p_hparams = problem.get_hparams(hparams)
    hparams.problem = problem
    hparams.problem_hparams = p_hparams
    return hparams

  def rescore(self, src_sentences, trg_sentences):
    bsz = src_sentences.shape[0]
    sentence_loss = self.mon_sess.run(
      self._sentence_loss,
      {self._inputs_var: src_sentences,
       self._targets_var: trg_sentences,
       self._pos_var: pos})
    return sentence_loss


def line_to_words(line, add_eos=False):
  line = line.strip()
  if not line:
    words = []
  else:
    words = map(int, line.split())
  if add_eos:
    words.append(EOS_ID)
  return np.array([words], dtype=np.int)


def batched_iter(src_path, trg_path=None, batch_size=1):
  if batch_size > 1:
    raise AttributeError("Batched decoding not implemented yet")
  with open(src_path) as src_reader:
    with open(trg_path) as trg_reader:
      for idx, (src_line, trg_line) in enumerate(zip(src_reader, trg_reader)):
        yield (np.array([idx], dtype=np.int),
               line_to_words(src_line), 
               line_to_words(trg_line, add_eos=True))


def sample2str(sample):
  trimmed = np.trim_zeros(sample)
  if len(trimmed) and trimmed[-1] == EOS_ID:
    trimmed = trimmed[:-1]
  return " ".join(map(str, trimmed))


class TextOutputHandler(object):

  def __init__(self, path):
    self.writer = open(path, "w")

  def write(self, idx, samples):
    self.writer.write("%s\n" % sample2str(samples[0][1]))

  def finish(self):
    self.writer.close()


class NbestOutputHandler(object):

  def __init__(self, path):
    self.path = path
    self.samples = {}

  def write(self, idx, samples):
    if idx in self.samples:
      self.samples[idx].extend(samples)
      self.samples[idx].sort(reverse=True, key=operator.itemgetter(0))
    else:
      self.samples[idx] = samples

  def finish(self):
    with open(self.path, "w") as writer:
      for idx in sorted(self.samples.iterkeys()):
        for score, sample in self.samples[idx]:
          writer.write("%d ||| %s ||| logprob=%f ||| %f\n" %
                       (idx, sample2str(sample), score, score))


def create_output_handlers():
  handlers = []
  for handler_name in FLAGS.outputs.split(","):
    path = FLAGS.output_path % handler_name
    if handler_name == "text":
      handlers.append(TextOutputHandler(path))
    elif handler_name == "nbest":
      handlers.append(NbestOutputHandler(path))
    else:
      raise AttributeError("Unknown output handler")
  return handlers


def main(_):
  tf.logging.set_verbosity(tf.logging.INFO)
  if FLAGS.verbose:
    tf.logging.set_verbosity(tf.logging.DEBUG)
  usr_dir.import_usr_dir(FLAGS.t2t_usr_dir)
  rescorer = Rescorer()
  output_handlers = create_output_handlers()
  for ids, src_sentences, trg_sentences in batched_iter(
      FLAGS.src_test, FLAGS.trg_test, FLAGS.batch_size):
    res = sampler.sample(src_sentences, trg_sentences)
    for idx, samples in zip(ids, res):
      samples.sort(reverse=True, key=operator.itemgetter(0))
      for ohandler in output_handlers:
        ohandler.write(idx, samples)
    break
  for ohandler in output_handlers:
    ohandler.finish()


if __name__ == "__main__":
  tf.app.run()
