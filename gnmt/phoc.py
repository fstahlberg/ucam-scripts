#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This script reads a word map and adds an additional column in sparse
feature format

<feat1>:<val1>,...,<featN>:<valN>

"""

import logging
import argparse
import sys
import operator
import re
import unicodedata

def voc2str(voc):
     return ' '.join([e[0] for e in sorted(voc.items(), key=operator.itemgetter(1))])

def get_regions(l, n, range_from, range_to):
    # Could be more efficient, this is more for simplicity
    region_size = float(n)/float(l)
    overlapped_regions = []
    for r in xrange(l):
        overlap = min(range_to, (r+1.0)*region_size) - max(range_from, r*region_size)
        if overlap/(range_to-range_from) >= 0.5:
            overlapped_regions.append(r)
    return overlapped_regions

def add_phoc_feat(feat, w, l, voc, start, unk_feat):
    for pos in xrange(len(w)):
        uni = w[pos]
        bi = w[pos:pos+2]
        if not uni in voc:
            feat[unk_feat] = 1
            continue
        for r in get_regions(l, len(w), pos, pos+1):
            feat[start + r*len(voc) + voc[uni]] = 1
        if bi in voc:
            for r in get_regions(l, len(w), pos, pos+2):
                feat[start + r*len(voc) + voc[bi]] = 1
    return feat
    
parser = argparse.ArgumentParser(description='Adds an additional column to the wmap '
                                 'which holds PHOC word representations in sparse '
                                 'vector format (feat1:val1,...,featN:valN). Usage: '
                                 'python phoc.py < wmap > wmap_with_phoc')
parser.add_argument('-l', "--load", default="", required=False,
                    help="Load PHOC definition from a file instead of building it")
parser.add_argument('-w', "--write", default="", required=False,
                    help="Write PHOC definition to a file")
parser.add_argument('-p', "--punctuation", default=";:?!\"+()[]@", required=False,
                    help="Punctuation characters which are not to be included in PHOC char set")
parser.add_argument('-bl', "--bigram_levels", default="2", required=False,
                    help="PHOC levels to which to add the bigrams (comma separated)")
parser.add_argument('-b', "--bigram_count", default=100, type=int, required=False,
                    help="PHOC adds the n most frequent bigrams to L2,")
parser.add_argument('-s', "--statistics_count", default=500000, type=int, required=False,
                    help="Collect statistics only over the first n words in wmap")
parser.add_argument('-c', "--min_char_count", default=1000, type=int, required=False,
                    help="Minimum number of occurrences for a char to get into PHOC char set")
parser.add_argument('-pi', "--max_punct_index", default=10000, type=int, required=False,
                    help="Single character words with id larger than this are not considered to be punctuation symbols")
parser.add_argument('-min', "--min_l", default=2, type=int, required=False,
                    help="Minimum histogram level (L1 is the first)")
parser.add_argument('-max', "--max_l", default=5, type=int, required=False,
                    help="Maximum histogram level (L1 is the first)")
parser.add_argument('-i','--inverse_wmap', help='Use this argument to use word maps with format "id word".'
                    ' Otherwise the format "word id" is assumed', action='store_true')
args = parser.parse_args()
NUMBER_CHARS = '-+°=:%.,¥$£'
NUMBER_PATTERN = re.compile('^[%s0-9]*[0-9]+[%s0-9]$' % (NUMBER_CHARS, NUMBER_CHARS))
EPS = '<epsilon>'
UNK = '<unk>'
BOS = '<s>'
EOS = '</s>'
FLAGS_NUMBER = 0
FLAGS_FIRST_UC = 1
FLAGS_ALL_UC = 2

bigram_levels = [2]
if args.bigram_levels:
    bigram_levels = [int(l) for l in args.bigram_levels.split(',')]

punct = {c: i for i,c in enumerate(args.punctuation)}
chars = {}
single_chars = {}
bigrams = {}
entries = []
n_lines = 0
stat_max = -1 if args.load else args.statistics_count

for line in sys.stdin:
    n_lines += 1
    parts = line.strip().split()
    if args.inverse_wmap:
        swp = parts[0]
        parts[0] = parts[1]
        parts[1] = swp
    w = parts[0].lower()
    if w:
        entries.append(parts)
        if n_lines > stat_max:
            continue
        if NUMBER_PATTERN.match(w): # its a number
            continue
        if w in [EPS, UNK, BOS, EOS]:
            continue
        if len(w) == 1:
            if not w in single_chars:
                single_chars[w] = n_lines
            continue
        chars[w[0]] = chars.get(w[0], 0) + 1
        for i in xrange(1, len(w)):
            chars[w[i]] = chars.get(w[i], 0) + 1
            bigrams[w[i-1:i+1]] = bigrams.get(w[i-1:i+1], 0) + 1

nonphoc_voc = [EPS, BOS, EOS, UNK]
nonphoc_start = 0
flags_start = len(nonphoc_voc)
l_voc = {}
l_start = {}

# Get the vocabularies
if not args.load: # derive them from the statistics
    mandatory_chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    char_idx = sorted(set([c for c in mandatory_chars + '.,:'] + [c for c in chars if chars[c] > args.min_char_count]))
    bigram_idx = [b[0] for b in sorted(bigrams.items(), 
                                       key=operator.itemgetter(1),
                                       reverse=True)[0:args.bigram_count]]
    punct_idx = [c for c in single_chars 
                   if not unicodedata.normalize('NFKD', unicode(c)) in mandatory_chars and single_chars[c] < args.max_punct_index]
    nonphoc_voc = {w: i for i,w in enumerate([EPS, BOS, EOS, UNK] + punct_idx)}
    nonphoc_start = 0
    flags_start = len(nonphoc_voc)
    this_start = flags_start + 3 # Three flags: number,first_upper_case,all_upper_case
    for l in xrange(args.min_l, args.max_l+1):
        voc = (char_idx + bigram_idx) if l in bigram_levels else char_idx
        l_voc[l] = {w: i for i,w in enumerate(voc)}
        l_start[l] = this_start
        this_start += l*len(voc)
else: # Load nonphoc_voc/start and l_voc/start from file
    with open(args.load) as f:
        regions = {}
        for line in f:
            key,val = line.split(":", 1)
            region,attr = key.strip().split("-", 1)
            if not region in regions:
                regions[region] = {}
            regions[region][attr] = val.strip().split()
        for region in regions:
            start = int(regions[region]['range'][0].split("-")[0])
            if region == 'flags':
                flags_start = start
            elif region == 'nonphoc':
                nonphoc_start = start
                nonphoc_voc = {w: i for i,w in enumerate(regions[region]['voc'])}
            else:
                try:
                    l = int(region[1:])
                    l_start[l] = start
                    l_voc[l] = {w: i for i,w in enumerate(regions[region]['voc'])}
                except:
                    logging.warning("Could not process region %s" % region)
        
if args.write: # Write configuration to file
    with open(args.write, "w") as f:
         f.write("nonphoc-range: %d-%d\n" % (nonphoc_start, nonphoc_start + len(nonphoc_voc)))
         f.write("flags-range: %d-%d\n" % (flags_start, flags_start + 3)) 
         for l in l_voc:
             f.write("l%d-range: %d-%d\n" % (l, l_start[l], l_start[l] + l*len(l_voc[l])))
         f.write("nonphoc-voc: %s\n" % voc2str(nonphoc_voc))
         f.write("flags-voc: <number> <first_upper_case> <all_upper_case>\n")
         for l in l_voc:
             f.write("l%d-voc: %s\n" % (l, voc2str(l_voc[l])))

# Apply to word map
for entry in entries:
    w = entry[0].lower()
    if w in nonphoc_voc:
        w_enc = "%d:1" % (nonphoc_voc[w] + nonphoc_start)
    else:
        feat = {}
        for l in l_voc:
            feat = add_phoc_feat(feat, w, l, l_voc[l], l_start[l], nonphoc_start + nonphoc_voc['<unk>'])
        # Add flags
        if NUMBER_PATTERN.match(w):
            feat[flags_start + FLAGS_NUMBER] = 1
        elif entry[0].isupper():
            feat[flags_start + FLAGS_ALL_UC] = 1
        elif entry[0][0].isupper():
            feat[flags_start + FLAGS_FIRST_UC] = 1
        w_enc = ','.join(["%d:1" % d for d in sorted(feat.iterkeys())])
    print(' '.join(entry + [w_enc]))
