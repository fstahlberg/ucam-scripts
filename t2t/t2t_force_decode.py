"""Forced decoding with t2t, collecting different statistics.
"""

import logging
import os

# Requires tensor2tensor
from tensor2tensor import models  # pylint: disable=unused-import
from tensor2tensor import problems as problems_lib  # pylint: disable=unused-import
from tensor2tensor.utils import usr_dir
from tensor2tensor.utils import registry
from tensor2tensor.utils import devices
from tensor2tensor.utils import trainer_lib
from tensor2tensor.data_generators.text_encoder import TextEncoder
from tensor2tensor.data_generators import problem  # pylint: disable=unused-import
from tensor2tensor.data_generators import text_encoder
import tensorflow as tf
from tensorflow.python.training import saver
from tensorflow.python.training import training
import numpy as np

import argparse

EOS_ID = 1
BOS_ID = 2

class DummyTextEncoder(TextEncoder):
  """Dummy TextEncoder implementation. The TextEncoder 
  implementation in tensor2tensor reads the vocabulary file in
  the constructor, which is not available inside SGNMT. This
  class can be used to replace the standard TextEncoder 
  implementation with a fixed vocabulary size. Note that this
  encoder cannot be used to translate between raw text and
  integer sequences.
  """

  def __init__(self, vocab_size, pop_id=None):
    super(DummyTextEncoder, self).__init__(num_reserved_ids=None)
    self._vocab_size = vocab_size

  def encode(self, s):
    raise NotImplementedError("Dummy encoder cannot be used to encode.")

  def decode(self, ids):
    raise NotImplementedError("Dummy encoder cannot be used to decode.")

  @property
  def vocab_size(self):
    return self._vocab_size

# Define flags from the t2t binaries
flags = tf.flags
FLAGS = flags.FLAGS
flags.DEFINE_string("schedule", "train_and_evaluate",
                    "Method of tf.contrib.learn.Experiment to run.")


def _initialize_t2t(t2t_usr_dir):
  tf.logging.info("Setting up tensor2tensor library...")
  tf.logging.set_verbosity(tf.logging.INFO)
  usr_dir.import_usr_dir(t2t_usr_dir)


def log_prob_from_logits(logits):
  """Softmax function."""
  return logits - tf.reduce_logsumexp(logits, keepdims=True, axis=-1)


def expand_input_dims_for_t2t(t, batched=False):
  """Expands a plain input tensor for using it in a T2T graph.

  Args:
    t: Tensor
    batched: Whether to expand on the left side

  Returns:
   Tensor `t` expanded by 1 dimension on the left and two dimensions
   on the right.
  """
  if not batched:
    t = tf.expand_dims(t, 0) # Because of batch_size
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


class Tensor2TensorAdaptor(object):

    def __init__(self,
                 model_name,
                 problem_name,
                 hparams_set_name,
                 checkpoint_dir,
                 src_vocab_size,
                 trg_vocab_size,
                 single_cpu_thread=False):
        logging.info("Initializing model at %s" % checkpoint_dir)
        self._single_cpu_thread = single_cpu_thread
        self._checkpoint_dir = checkpoint_dir
        self.src_vocab_size = src_vocab_size
        self.trg_vocab_size = trg_vocab_size
        if not model_name or not problem_name or not hparams_set_name:
            tf.logging.fatal(
                "Please specify t2t_model, t2t_problem, and t2t_hparams_set!")
            raise AttributeError
        self.consumed = []
        self.src_sentence = []
        predictor_graph = tf.Graph()
        with predictor_graph.as_default() as g:
            hparams = trainer_lib.create_hparams(hparams_set_name)
            self._add_problem_hparams(hparams, problem_name)
            translate_model = registry.model(model_name)(
                hparams, tf.estimator.ModeKeys.EVAL)
            self._inputs_var = tf.placeholder(dtype=tf.int32, shape=[None],
                                              name="sgnmt_inputs")
            self._targets_var = tf.placeholder(dtype=tf.int32, shape=[None], 
                                               name="sgnmt_targets")
            features = {"inputs": expand_input_dims_for_t2t(self._inputs_var), 
                        "targets": expand_input_dims_for_t2t(self._targets_var)}
            translate_model.prepare_features_for_infer(features)
            translate_model._fill_problem_hparams_features(features)
            logits, _ = translate_model(features)
            logits = tf.squeeze(logits, [0, 2, 3])
            self._log_probs = log_prob_from_logits(logits)
            self.mon_sess = self.create_session()

    def _add_problem_hparams(self, hparams, problem_name):
        problem = registry.problem(problem_name)
        problem._encoders = {
            "inputs": DummyTextEncoder(vocab_size=self.src_vocab_size),
            "targets": DummyTextEncoder(vocab_size=self.trg_vocab_size)
        }
        p_hparams = problem.get_hparams(hparams)
        hparams.problem = problem
        hparams.problem_hparams = p_hparams
        return hparams

    def _session_config(self):
        """Creates the session config with t2t default parameters."""
        graph_options = tf.GraphOptions(optimizer_options=tf.OptimizerOptions(
            opt_level=tf.OptimizerOptions.L1, do_function_inlining=False))
        if self._single_cpu_thread:
            config = tf.ConfigProto(
                intra_op_parallelism_threads=1,
                inter_op_parallelism_threads=1,
                allow_soft_placement=True,
                graph_options=graph_options,
                log_device_placement=False)
        else:
            gpu_options = tf.GPUOptions(
                per_process_gpu_memory_fraction=0.95)
            config = tf.ConfigProto(
                allow_soft_placement=True,
                graph_options=graph_options,
                gpu_options=gpu_options,
                log_device_placement=False)
        return config

    def create_session(self):
        """Creates a MonitoredSession for this predictor."""
        try:
            if os.path.isdir(self._checkpoint_dir):
                checkpoint_path = saver.latest_checkpoint(self._checkpoint_dir)
            else:
                checkpoint_path = self._checkpoint_dir
                tf.logging.info("%s is not a directory. Interpreting as direct "
                             "path to checkpoint..." % checkpoint_path)
            return training.MonitoredSession(
                session_creator=training.ChiefSessionCreator(
                    checkpoint_filename_with_path=checkpoint_path,
                    config=self._session_config()))
        except tf.errors.NotFoundError as e:
            tf.logging.fatal("Could not find all variables of the computation "
                "graph in the T2T checkpoint file. This means that the "
                "checkpoint does not correspond to the model specified in "
                "SGNMT. Please double-check pred_src_vocab_size, "
                "pred_trg_vocab_size, and all the t2t_* parameters.")
            raise AttributeError("Could not initialize TF session.")
                
    def get_log_probs(self, src_sentence, trg_sentence):
        """Call the T2T model in self.mon_sess."""
        log_probs = self.mon_sess.run(self._log_probs,
            {self._inputs_var: src_sentence,
             self._targets_var: trg_sentence})
        return log_probs


class GlueModifier(object):
  def __init__(self, adaptor):
    self._adaptor = adaptor

  def get_log_probs(self, src_document, trg_document):
    src_sentences = [[]]
    trg_sentences = [[]]
    for tok in src_document:
      if tok == BOS_ID:
        src_sentences.append([])
      else:
        src_sentences[-1].append(tok)
    for tok in trg_document:
      if tok == BOS_ID:
        trg_sentences[-1].append(EOS_ID)
        trg_sentences.append([])
      else:
        trg_sentences[-1].append(tok)
    all_log_probs = [self._adaptor.get_log_probs(s, t) 
                     for s, t in zip(src_sentences, trg_sentences)]
    for log_probs in all_log_probs:
      log_probs[BOS_ID] = log_probs[EOS_ID]
    return np.concatenate(all_log_probs, axis=0)
   
 
class OutputHandler(object):

  def __init__(self, adaptors):
    self._adaptors = adaptors

  def get_headers(self):
    """Get names of statistics computed by this output handler

    Return:
      List of strings
    """
    raise NotImplemented()

  def process(self, src_sentence, trg_sentence, log_probs):
    """Computes statistics for the sentence pair.

    Args:
      src_sentence: Integer list with source sentence
      trg_sentence: Integer list with target sentence
      log_probs: List of [trg_len, vocab_size] arrays with log probs
                 (one from each adaptor)
    
    Return:
      List of list of floats.
    """
    raise NotImplemented()


class WordsOutputHandler(OutputHandler):

  def get_headers(self):
    return ["trg_word"]

  def process(self, src_sentence, trg_sentence, log_probs):
    return [[w] for w in trg_sentence]


class SentenceIdOutputHandler(OutputHandler):

  def __init__(self, adaptors):
    self._adaptors = adaptors
    self.sen_id = -1

  def get_headers(self):
    return ["sen_idx"]

  def process(self, src_sentence, trg_sentence, log_probs):
    self.sen_id += 1
    return [[self.sen_id] for w in trg_sentence]


class WordIdOutputHandler(OutputHandler):

  def get_headers(self):
    return ["word_idx"]

  def process(self, src_sentence, trg_sentence, log_probs):
    return [[i] for i, _ in enumerate(trg_sentence)]


class KLDivergenceOutputHandler(OutputHandler):

  def get_headers(self):
    n = len(self._adaptors)
    headers = []
    for p in xrange(n):
      for q in xrange(n):
        if p != q:
          headers.append("kl-%d-%d" % (p, q))
    return headers

  def _kl(self, p_log_probs, q_log_probs):
    return np.sum(np.exp(p_log_probs) * (p_log_probs - q_log_probs))

  def process(self, src_sentence, trg_sentence, log_probs):
    n = len(self._adaptors)
    ret = []
    for idx, word in enumerate(trg_sentence):
      ret.append([])
      for p in xrange(n):
        for q in xrange(n):
          if p != q:
            ret[-1].append(self._kl(log_probs[p][idx], log_probs[q][idx]))
    return ret


class LogProbOutputHandler(OutputHandler):

  def get_headers(self):
    return ["log_prob-%d" % i for i, _ in enumerate(self._adaptors)]

  def process(self, src_sentence, trg_sentence, log_probs):
    ret = []
    for idx, word in enumerate(trg_sentence):
      ret.append([log_prob[idx, word] for log_prob in log_probs])
    return ret


def main():
  parser = argparse.ArgumentParser(description='Force decoding')
  parser.add_argument('-tm', '--t2t_models', help='Comma-separated list of T2T models', required=True)
  parser.add_argument('-tp', '--t2t_problems', help='Comma-separated list of T2T problems', required=True)
  parser.add_argument('-th', '--t2t_hparams_sets', help='Comma-separated list of T2T hparams sets', required=True)
  parser.add_argument('-tc', '--t2t_checkpoints', help='Paths to T2T checkpoints.', required=True)
  parser.add_argument('-tu', '--t2t_usr_dir', help='usr directory', required=True)
  parser.add_argument('-sv', '--src_vocab_size', help='Source vocabulary size', required=True, type=int)
  parser.add_argument('-tv', '--trg_vocab_size', help='Target vocabulary size', required=True, type=int)
  parser.add_argument('-src', '--src_sentences', help='Source sentences', required=True)
  parser.add_argument('-trg', '--trg_sentences', help='Target sentences', required=True)
  parser.add_argument('-of', '--output_file', help='Output file', required=True)
  parser.add_argument('-m', '--modifiers', help='Comma-separated list of modifiers. g: glue model', default="")
  parser.add_argument('-oh', '--output_handlers', help='Output handlers. Comma-separated list of logprob,kl,word,word_idx,sen_idx', required=True)
  parser.add_argument("--write_headers", help="Write name of statistics in first line of the output file", action="store_true")
  args = parser.parse_args()

  _initialize_t2t(args.t2t_usr_dir)
  adaptors = []
  if not args.modifiers:
    modifiers = [""] * len(args.t2t_models.split(","))
  else:
    modifiers = args.modifiers.split(",")
  for model_name, modifier, problem_name, hparams_set_name, checkpoint_dir in zip(
        args.t2t_models.split(","),
        modifiers,
        args.t2t_problems.split(","),
        args.t2t_hparams_sets.split(","),
        args.t2t_checkpoints.split(",")):
    adaptor = Tensor2TensorAdaptor(model_name,
                                   problem_name,
                                   hparams_set_name,
                                   checkpoint_dir,
                                   args.src_vocab_size,
                                   args.trg_vocab_size)
    if "g" in modifier:
      adaptor = GlueModifier(adaptor)
    adaptors.append(adaptor)

  output_handlers = []
  for handler_name in args.output_handlers.split(","):
    if handler_name == "word":
      h = WordsOutputHandler(adaptors)
    elif handler_name == "kl":
      h = KLDivergenceOutputHandler(adaptors)
    elif handler_name == "sen_idx":
      h = SentenceIdOutputHandler(adaptors)
    elif handler_name == "word_idx":
      h = WordIdOutputHandler(adaptors)
    elif handler_name == "log_prob":
      h = LogProbOutputHandler(adaptors)
    else:
      tf.logging.fatal("Unknown output handler '%s'" % handler_name)
      raise AttributeError
    output_handlers.append(h)
  
  tf,logging.info("Start writing output file...")
  with open(args.output_file, "w") as writer:
    if args.write_headers:
      headers = []
      for oh in output_handlers:
        headers.extend(oh.get_headers())
      writer.write("%s\n" % "\t".join(headers))  
    with open(args.src_sentences) as src_reader:
      with open(args.trg_sentences) as trg_reader:
        for sen_idx, (src_line, trg_line) in enumerate(zip(src_reader, trg_reader)):
          src_sentence = map(int, src_line.strip().split())
          trg_sentence = map(int, trg_line.strip().split()) + [EOS_ID]
          log_probs = [a.get_log_probs(src_sentence, trg_sentence) for a in adaptors]
          stats = [h.process(src_sentence, trg_sentence, log_probs) for h in output_handlers]
          for i in xrange(len(trg_sentence)):
            line = []
            for handler_stats in stats:
              line.extend(handler_stats[i])
            writer.write("\t".join(map(str, line)))
            writer.write("\n")
          writer.write("\n")
          if sen_idx % 10 == 0:
            tf.logging.info("Processed %d sentences" % sen_idx)


if __name__ == '__main__':
  main()



