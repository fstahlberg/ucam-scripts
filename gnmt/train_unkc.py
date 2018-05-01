"""This script can be used to train the parameters of the unkc predictor
in SGNMT.
"""

import logging
import argparse
import sys

parser = argparse.ArgumentParser(description='Trains the lambda parameters of the unkc predictor.'
                                 'Usage: python train_unkc.py -s <source-train> -t <target-train>')
parser.add_argument('-vs', "--vocab_source", default=50003, type=int, required=False,
                    help="Source vocabulary size")
parser.add_argument('-vt', "--vocab_target", default=50003, type=int, required=False,
                    help="Target vocabulary size")
parser.add_argument('-n', "--n_lambda", default=6, type=int, required=False,
                    help="Train separate lambdas for 0,1,..,>=n source UNKs.")
parser.add_argument('-s','--source', help='Source training sentences (indexed)', required=True)
parser.add_argument('-t','--target', help='Source training sentences (indexed)', required=True)
args = parser.parse_args()

cnts = [[] for _ in xrange(args.n_lambda)]
with open(args.source) as sf:
    with open(args.target) as tf:
        for sline in sf:
            tline = tf.readline()
            scnt = len([1 for w in sline.strip().split() if int(w) >= args.vocab_source])
            tcnt = len([1 for w in tline.strip().split() if int(w) >= args.vocab_target])
            cnts[min(scnt, len(cnts)-1)].append(tcnt)

print(",".join([str(sum(cnt) / float(len(cnt))) for cnt in cnts]))

