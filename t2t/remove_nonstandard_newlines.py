# coding=utf-8

import sys, traceback
import argparse
import codecs

reader = codecs.getreader('utf8')(sys.stdin)
writer = codecs.getwriter('utf-8')(sys.stdout)

delete = [u'\x0b', u'\x0c', u'\x0d', u'\x1c', u'\x1d', u'\x1e', u'\x1f', u'\x85', u'\u2028']

for line in reader:
  for c in delete:
    line = line.replace(c, '')
  writer.write(line)
