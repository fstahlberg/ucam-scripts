"""Simple grid search
"""

import sys, os, time, re
import logging
logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s')
import argparse
import shutil
from operator import itemgetter
from random import shuffle


parser = argparse.ArgumentParser(description='Uses simple grid search for MERT '
                                 'tuning of SGNMT predictor weights.')
parser.add_argument('-d','--work_dir', help='Working directory',
                    required=True)
parser.add_argument('-n','--num_parts', help='Number of grid jobs', default=100, type=int)
parser.add_argument('-r','--range', help='Range of sentence IDs (e.g. 1:2737)',
                    required=True)
parser.add_argument('-b','--bleu_cmd', help='BLEU command. Must read indexed sentences from stdin',
                    required=True)
parser.add_argument('-c','--config_file', help='SGNMT configuration file. Must not include predictor_weights or outputs',
                    required=True)
parser.add_argument('-g','--groups', help='Use this to share predictor weights. Comma separated list of ints, same numbers'
                    'for predictors which share weights. Default: no sharing (ie. 1,2,3,4,5...)',
                    default='',
                    required=False)
parser.add_argument('-s','--decode_script', help='path to one of the decode_on_grid_cpu*.sh scripts which should be used '
                    'for distributed decoding',
                    default='../scripts/grid/decode_on_grid_cpu.sh',
                    required=False)
parser.add_argument('-i','--iter', help='Number of iteration spent to optimize a single dimension',
                    default=20,
                    required=False)
args = parser.parse_args()


def objective(point):
    """Definition of the objective function for hyperopt """
    params = {n: point[i] for i,n in enumerate(group_names)}
    pred_weights = ','.join([str(params['group%d' % g] if g >= 0 else 1.0-params['group%d' % -g]) for g in groups])
    logging.info("Evaluate data point: %s (predictor weights: %s)" % (point, pred_weights))
    sgnmt_dir = "%s/sgnmt" % args.work_dir
    config_file = "%s/config.ini" % sgnmt_dir
    done_file = "%s/DONE" % sgnmt_dir
    try:
        shutil.rmtree(sgnmt_dir)
    except:
        pass
    os.mkdir(sgnmt_dir)
    shutil.copyfile(args.config_file, config_file)
    with open(config_file, "a") as f:
        f.write("outputs: text,nbest\n")
        f.write("predictor_weights: %s\n" % pred_weights)
    cmd = "%s %d %s %s %s" % (args.decode_script, args.num_parts, args.range, config_file, sgnmt_dir)
    logging.info("Start decoding: %s" % cmd)
    os.system(cmd)
    logging.info("Waiting for %s..." % done_file)
    while not os.path.exists(done_file):
        time.sleep(10)
    eval_cmd = "cat %s/out.text | %s > %s/bleu" % (sgnmt_dir, args.bleu_cmd, sgnmt_dir)
    logging.info("Start evaluation: %s" % eval_cmd)
    os.system(eval_cmd)
    bleu_score = 0.0
    with open("%s/bleu" % sgnmt_dir) as f:
        for line in f:
            logging.info("bleu script stdout: %s" % line.strip())
            if bleu_score <= 0.0:
                match = re.match( r'^BLEU = ([.0-9]+),', line)
                if match:
                    bleu_score = float(match.group(1))
    logging.info("pred_weights: %s bleu_score: %f" % (pred_weights, bleu_score))
    return -bleu_score

n_predictors = -1
with open(args.config_file) as f:
    for line in f:
        parts = line.split(':', 1)
        if parts[0].strip() == 'predictors':
            n_predictors = len(parts[1].split(','))
            break
if n_predictors < 0:
    logging.fatal("Could not find 'predictors' key in config file")
    sys.exit()

groups = [int(i) for i in args.groups.split(',')] if args.groups else range(n_predictors)

if len(groups) != n_predictors:
    logging.fatal("%d predictors found, but %d group entries!" % (n_predictors, len(groups)))
    sys.exit()

group_names = ['group%d' % i for i in set([abs(g) for g in groups])]
try:
    os.mkdir(args.work_dir)
except:
    logging.info("Working directory already exists...")

# minimize the objective over the space
cur_point = [0.5] * len(group_names)
last_val = objective(cur_point)

while True:
    for dim in xrange(len(cur_point)):
        logging.info("Optimizing %s" % group_names[dim])
        vals = [(cur_point[dim], last_val)]
        for _ in xrange(args.iter):
            best_pos, best_val = vals[0]
            lower_pos = 0.0
            upper_pos = 1.0
            for pos, val in vals: # Find values close to best_pos
                if pos < best_pos:
                    if pos > lower_pos:
                        lower_pos = pos
                elif pos > best_pos:
                    if pos < upper_pos:
                        upper_pos = pos
            test_pos = [lower_pos, upper_pos]
            shuffle(test_pos)
            for bound_pos in test_pos:
                next_pos = (best_pos + bound_pos) / 2.0
                cur_point[dim] = next_pos
                next_val = objective(cur_point)
                vals.append((next_pos, next_val))
                if next_val < best_val:
                    break
            vals.sort(key=itemgetter(1))
        
print cur_point
