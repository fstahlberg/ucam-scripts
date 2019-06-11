"""Improve sentences with document-level LM
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
from collections import defaultdict

EOS_ID = 1
BOS_ID = 2
model_weights = None

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
                 trg_vocab_size,
                 single_cpu_thread=False):
        tf.logging.info("Initializing model at %s" % checkpoint_dir)
        self._single_cpu_thread = single_cpu_thread
        self._checkpoint_dir = checkpoint_dir
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

            self._targets_var = tf.placeholder(dtype=tf.int32, shape=[None], 
                                               name="sgnmt_targets")
            self._targets_seg_var = tf.placeholder(dtype=tf.int32, shape=[None], 
                                                   name="sgnmt_targets_seg")
            self._targets_pos_var = tf.placeholder(dtype=tf.int32, shape=[None],
                                                   name="sgnmt_targets_pos")
            features = {
                "targets": expand_input_dims_for_t2t(self._targets_var),
                "targets_seg": tf.expand_dims(self._targets_seg_var, 0),
                "targets_pos": tf.expand_dims(self._targets_pos_var, 0)
            }

            translate_model.prepare_features_for_infer(features)
            translate_model._fill_problem_hparams_features(features)
            logits, _ = translate_model(features)
            logits = tf.squeeze(logits, [0, 2, 3])
            log_probs = log_prob_from_logits(logits)
            self._log_prob = tf.reduce_sum(gather_2d(log_probs, tf.expand_dims(self._targets_var, 1)))
            self.mon_sess = self.create_session()

    def _add_problem_hparams(self, hparams, problem_name):
        problem = registry.problem(problem_name)
        problem._encoders = {
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
                
    def get_log_prob(self, trg_sentence):
        """Call the T2T model in self.mon_sess."""
        trg_seg, trg_pos = self._gen_seg_and_pos(trg_sentence)
        log_prob = self.mon_sess.run(self._log_prob,
            {self._targets_var: trg_sentence,
             self._targets_seg_var: trg_seg,
             self._targets_pos_var: trg_pos})
        return log_prob

    def _gen_seg_and_pos(self, glued):
        seg = []
        pos = []
        cur_seg = 1
        cur_pos = 0
        for w in glued:
            seg.append(cur_seg)
            pos.append(cur_pos)
            if w == BOS_ID:
                cur_seg += 1
                cur_pos = 0
            else:
                cur_pos += 1
        return seg, pos

class Hypo(object):

  def __init__(self, glued, nbest_score, t2t_score):
    self.glued = glued
    self.scores = [t2t_score, nbest_score, float(len(glued))]

  def total_score(self):
    return sum(s*w for s, w in zip(self.scores, model_weights))

  def str_glued(self):
    return " ".join(map(str, self.glued))


def get_hypo(ranks, doc_nbest, adaptor, skip_scoring=False):
  glued = []
  nbest_score = 0.0
  for rank, nbest in zip(ranks, doc_nbest):
    glued.append(BOS_ID)
    glued.extend(nbest[rank][1])
    nbest_score += nbest[rank][0]
  glued = glued[1:]
  if skip_scoring:
    tf.logging.info("Skipping scoring...")
    t2t_score = 0.0
  else:
    t2t_score = adaptor.get_log_prob(glued)
  return Hypo(glued, nbest_score, t2t_score)


def main():
  global model_weights
  parser = argparse.ArgumentParser(description='Refines sentences with a document-level LM')
  parser.add_argument('-tm', '--t2t_model', help='T2T models', required=True)
  parser.add_argument('-tp', '--t2t_problem', help='T2T problems', required=True)
  parser.add_argument('-th', '--t2t_hparams_set', help='T2T hparams set', required=True)
  parser.add_argument('-tc', '--t2t_checkpoint', help='Path to T2T checkpoint.', required=True)
  parser.add_argument('-tu', '--t2t_usr_dir', help='usr directory', required=True)
  parser.add_argument('-tv', '--trg_vocab_size', help='Target vocabulary size', required=True, type=int)
  parser.add_argument('-src', '--src_glued', help='Source documents (Glued)', required=True)
  parser.add_argument('-trg', '--trg_nbest', help='Target nbest list of sentences', required=True)
  parser.add_argument('-op', '--output_path', help='Output path with %s placeholder', required=True)
  parser.add_argument('-of', '--output_formats', help='Comma-separated list of output formats', required=False, default="nbest,text")
  parser.add_argument('-r', '--range', help='Range of document IDs (inclusive, starting with 1)', required=False, default="")
  parser.add_argument('-w', '--weights', help='Weight vector: t2t_score,nbest_weight,word_count', required=True)
  parser.add_argument('-pt', '--prune_threshold', help='Lower values lead to more pruning', required=False, default=1.5, type=float)
  parser.add_argument('-n', '--nbest', help='Number of entries in output nbest list', required=False, default=10, type=int)
  parser.add_argument('-min', '--min_sen', help='If document has less than this sentences, skip', required=False, default=3, type=int)
  parser.add_argument('-max', '--max_sen', help='If document has less than this sentences, skip', required=False, default=200, type=int)
  args = parser.parse_args()

  model_weights = map(float, args.weights.split(","))

  _initialize_t2t(args.t2t_usr_dir)
  adaptor = Tensor2TensorAdaptor(args.t2t_model,
                                 args.t2t_problem,
                                 args.t2t_hparams_set,
                                 args.t2t_checkpoint,
                                 args.trg_vocab_size)
  if not args.range:
    from_doc_idx = -1
    to_doc_idx = 1000000
  else:
    from_doc_idx, to_doc_idx = map(lambda x: int(x) - 1, args.range.split(":"))
  tf.logging.info("Loading nbest file...")
  trg_nbest = defaultdict(lambda: [])
  with open(args.trg_nbest) as trg_reader:
    for line in trg_reader:
      parts = line.split("|")
      idx = int(parts[0].strip())
      trg_nbest[idx].append((float(parts[-1].strip()), map(int, parts[3].strip().split())))
  with open(args.output_path % "text", "w") as plain_writer:
    with open(args.output_path % "nbest", "w") as nbest_writer:
      trg_sen_idx = 0
      with open(args.src_glued) as src_reader:
        for doc_idx, glued_line in enumerate(src_reader):
          n_sentences = glued_line.strip().split().count(str(BOS_ID)) + 1
          if doc_idx >= from_doc_idx and doc_idx <= to_doc_idx:
            current_ranks = [0] * n_sentences
            doc_nbest = [trg_nbest[idx] for idx in xrange(trg_sen_idx, trg_sen_idx+n_sentences)]
            base_hypo = get_hypo(current_ranks, doc_nbest, adaptor, skip_scoring=n_sentences > args.max_sen)
            best_score = base_hypo.total_score()
            ops = []
            hypos = [base_hypo]
            tf.logging.info("Document id=%d n_sentences=%d base_score=%f %s" % (doc_idx+1, n_sentences, best_score, base_hypo.scores))
            if n_sentences >= args.min_sen and n_sentences <= args.max_sen:
              for i, nbest_single in enumerate(doc_nbest):
                first_best_score = nbest_single[0][0]
                for j in xrange(1, len(nbest_single)):
                  ops.append((first_best_score - nbest_single[j][0], i, j))
              ops.sort()
            for op in ops:
              if op[0] > args.prune_threshold:
                break
              pos, new_rank = op[1:]
              old_rank = current_ranks[pos]
              tf.logging.info("%d -> %d at pos %d (%f)" % (old_rank, new_rank, pos, op[0]))
              current_ranks[pos] = new_rank
              hypo = get_hypo(current_ranks, doc_nbest, adaptor)
              hypos.append(hypo)
              if hypo.total_score() > best_score:
                best_score = hypo.total_score()
                tf.logging.info("New best: %f %s" % (best_score, hypo.scores))
              else:
                current_ranks[pos] = old_rank
            hypos.sort(key=lambda h: -h.total_score())
            tf.logging.info("Decoded (ID: %d): %s" % (doc_idx+1, hypos[0].str_glued()))
            tf.logging.info("Stats (ID: %d): score=%f num_expansions=%d" % (doc_idx+1, hypos[0].total_score(), len(hypos)))
            if "text" in args.output_formats:
              plain_writer.write("%s\n" % hypos[0].str_glued())
            if "nbest" in args.output_formats:
              for hypo in hypos[:args.nbest]:
                nbest_writer.write("%d ||| %s ||| t2t=%f sennbest=%f wc=%f ||| %f\n" % (doc_idx, hypo.str_glued(), hypo.scores[0], hypo.scores[1], hypo.scores[2], hypo.total_score()))

          trg_sen_idx += n_sentences

if __name__ == '__main__':
  main()



