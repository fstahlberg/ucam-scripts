'''
If different subsystems were trained using different wmaps, GNMT
requires a indexmap which maps the main word indices (corresponding
to the NMT wmap) to these indices. This script creates an indexmap
from two wmaps.
'''

import logging
import argparse

parser = argparse.ArgumentParser(description='Creates an index map out of two word maps, '
                     'i.e. a map from primary word map indices to secondary word map indices')
parser.add_argument('-p','--primary_wmap', help='Primary word map', required=True)
parser.add_argument('-s','--secondary_wmap', help='Secondary word map', required=True)
parser.add_argument('-u','--unk_id', type=int, help='If positive, map entries which are not in sec. map to this', default=-1)
args = parser.parse_args()

with open(args.secondary_wmap) as secondary_wmap_file:
    secondary_wmap = dict(line.strip().split(None, 1) for line in secondary_wmap_file)

with open(args.primary_wmap) as primary_wmap_file:
    for line in primary_wmap_file:
        word, primary_idx = line.strip().split(None, 1)
        if not word in secondary_wmap:
            logging.error("Could not find '%s' in secondary wmap!" % word)
            if args.unk_id >= 0:
                logging.warn("Mapping %s to UNK id %d" % (primary_idx, args.unk_id))
                print("%s %d" % (primary_idx, args.unk_id))
        else:
            print("%s %s" % (primary_idx, secondary_wmap[word]))

