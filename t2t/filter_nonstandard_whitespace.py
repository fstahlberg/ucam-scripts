# coding=utf-8
r"""Prints out all line numbers with no whitespace besides blanks."""

import sys
import re
import codecs

reader = codecs.getreader('utf8')(sys.stdin)

for n,line in enumerate(reader):
  #if re.sub(r"\s+", "", line, flags=re.UNICODE) == ''.join(line.strip().split()):
  if ''.join(line.strip().split(' ')) == ''.join(line.strip().split()):
    print(n)

