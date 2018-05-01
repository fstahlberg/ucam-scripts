#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division

import sys
import codecs
import argparse
from collections import defaultdict

# hack for python2/3 compatibility
from io import open
argparse.open = open

# python 2/3 compatibility
if sys.version_info < (3, 0):
  sys.stderr = codecs.getwriter('UTF-8')(sys.stderr)
  sys.stdout = codecs.getwriter('UTF-8')(sys.stdout)
  sys.stdin = codecs.getreader('UTF-8')(sys.stdin)

import codecs

parser = argparse.ArgumentParser(description='Creates an FST in text format which converts sequences '
                                 'of characters to (sub)word units.')
parser.add_argument('--output', '-o', type=argparse.FileType('w'), default=sys.stdout,
                    metavar='PATH',
                    help="Output file (default: standard output)")
parser.add_argument('--wmap', '-w', type=argparse.FileType('r'), default=sys.stdin,
                    metavar='PATH',
                    help="Path to word map (default: standard input).")
parser.add_argument('--cmap', '-c', type=argparse.FileType('r'),
                    metavar='PATH',
                    required=True,
                    help="Path to the character map.")
parser.add_argument('-e','--explicit_eow', help='If not set, add </w> to each entry which is not '
                    'tagged with <b>, <m>, or <e>', action='store_true')
parser.add_argument('-u','--unk_id', help='UNK ID. If set to 0, do not add the UNK paths to the FST',
                    default=0, type=int)
char_unk = "999999998"

args = parser.parse_args()

cmap = dict(tuple(line.split()) for line in args.cmap)

next_free_id = 1
char_state = -1
for line in args.wmap:
    parts = line.strip().split()
    if len(parts) != 2:
        continue
    w,i = parts
    if i == "0":
        continue
    if w in ['<s>', '</s>']:
        args.output.write("0 0 %s %s\n" % (cmap[w], i))
    elif w[:3] in ['<b>', '<m>', '<e>']:
        if char_state < 0:
            char_state = next_free_id
            next_free_id += 2
            args.output.write("%d 0 %s 0\n" % (char_state+1, cmap["</w>"]))
        args.output.write("%d %d %s %s\n" % (0 if w[1] == 'b' else char_state,
                                             (char_state+1) if w[1] == 'e' else char_state,
                                             cmap.get(w[3:], char_unk),
                                             i))
    else: # full word or subword unit
        if not args.explicit_eow:
            chars = w
            last_char = '</w>'
        elif w[-4:] == '</w>':
            chars = w[:-4]
            last_char = '</w>'
        else:
            chars = w[:-1]
            last_char = w[-1]
        last_state = 0
        input_label = i
        for c in chars:
            args.output.write("%d %d %s %s\n" % (last_state, 
                                                 next_free_id, 
                                                 cmap.get(c, char_unk),
                                                 input_label))
            last_state = next_free_id
            next_free_id += 1
            input_label = "0"
        args.output.write("%d %d %s %s\n" % (last_state, 
                                             0,
                                             cmap.get(last_char, char_unk), 
                                             input_label))

# Add UNK transition
if args.unk_id:
    unk_state = next_free_id
    next_free_id += 1
    for k,i in cmap.iteritems():
        if i != "0" and not k in ['<s>', '</s>', '</w>', '<eps>', '<epsilon>']:
            args.output.write("%d %d %s %s\n" % (0, unk_state, i, args.unk_id))
            args.output.write("%d %d %s 0\n" % (unk_state, unk_state, i))
    args.output.write("%d %d %s 0\n" % (unk_state, 0, cmap['</w>']))
            

args.output.write("0\n") 
