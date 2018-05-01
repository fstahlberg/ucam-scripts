# coding=utf-8
r"""Tokenize Chinese with jieba."""

import jieba
import sys
import codecs

reader = codecs.getreader('utf8')(sys.stdin)
writer = codecs.getwriter('utf-8')(sys.stdout)

# do not use codecs.getreader() because of this:
# https://stackoverflow.com/questions/17273598/python-codecs-line-ending

for zh_txt in sys.stdin:
  zh_txt = zh_txt.decode("UTF-8")
  zh_txt = "".join(zh_txt.split())
  zh_txt = " ".join(jieba.cut(zh_txt, cut_all=False))
  writer.write(zh_txt + "\n")


