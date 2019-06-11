# coding=utf-8
r"""Apply edit operations from editt2t to the initial sentences."""

import argparse
import sys

parser = argparse.ArgumentParser(description='Read edit operations from stdin and apply them to sentences in trg_test.')
parser.add_argument('-t','--trg_test', help='Text file with initial sentences.', required=False)
args = parser.parse_args()


EOS_ID = 1


def ins_op(s, pos, token):
  """Returns a copy of s after an insertion."""
  return s[:pos] + [token] + s[pos:]


def sub_op(s, pos, token):
  """Returns a copy of s after a substitution."""
  ret = list(s)
  ret[pos] = token
  return ret


def del_op(s, pos):
  """Returns a copy of s after a deletion."""
  return s[:pos] + s[pos+1:]


def apply_ops(line_nr, line):
  ops = map(int, line.strip().split())
  sentence = [EOS_ID]
  if trg_sentences is not None:
    sentence = trg_sentences[line_nr]
  for op in ops:
    pos = (op // 100000) % 1000
    token = op % 100000
    op_type = op // 100000000  
    if op_type == 1:  # Insertion
      sentence = ins_op(sentence, pos, token)
    elif op_type == 2:  # Substitution
      sentence = sub_op(sentence, pos, token)
    elif op_type == 3:  # Deletion
      sentence = del_op(sentence, pos)
    else:
      sys.exit("Illegal operation %d" % op)
  if sentence and sentence[-1] == EOS_ID:
    sentence = sentence[:-1]
  return " ".join(map(str, sentence))


trg_sentences = None
if args.trg_test:
  trg_sentences = []
  with open(args.trg_test) as f:
    for line in f:
      trg_sentences.append(map(int, line.strip().split()) + [EOS_ID])

for line_nr, line in enumerate(sys.stdin):
  if "|" in line:  # n-best list format
    parts = line.strip().split("|")
    parsed = apply_ops(int(parts[0].strip()), parts[3])
    print("|".join(parts[:3] + [" " + parsed + " "] + parts[4:]))
  else:
    print(apply_ops(line_nr, line))

