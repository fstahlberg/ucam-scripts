# coding=utf-8
r"""Cleans up raw text corpora."""

import sys
import argparse
import codecs
from langdetect import detect_langs

parser = argparse.ArgumentParser(description='Cleans up raw text corpora.')
parser.add_argument('-sd','--src_data', help='Source data')
parser.add_argument('-sl','--src_language', help='Source language')
parser.add_argument('-td','--trg_data', help='Target data')
parser.add_argument('-tl','--trg_language', help='Target language')
parser.add_argument('-o','--output_prefix', help='Prefix for output files')
parser.add_argument('-r','--max_ratio', default=0.0, help='Maximum ratio between src and trg length')
parser.add_argument('-lo_l','--min_length', default=1, help='Minimum number of words')
parser.add_argument('-hi_l','--max_length', default=150, help='Maximum number of words')
args = parser.parse_args()

src_reader = codecs.getreader('utf8')(open(args.src_data))
src_writer = codecs.getwriter('utf-8')(open("%s.clean.%s" % (args.output_prefix, args.src_language), "w"))
sys.stdout = codecs.getwriter('utf-8')(sys.stdout)


def check_mono(txt, lang, length):
  if length > args.max_length:
    print("TOO_LONG %s %d: %s" % (lang, length, txt))
    return False
  if length < args.min_length:
    print("TOO_SHORT %s %d: %s" % (lang, length, txt))
    return False
  try:
    result = detect_langs(txt)
  except Exception as e:
    print("LANG_DETECT_FAIL %s %s: %s" % (lang, e, txt))
    return False
  detected_lang = result[0].lang[:2] if result else "None"
  if detected_lang == "ko" and lang == "zh":
    detected_lang = "zh"
  if lang != detected_lang:
    print("WRONG_LANG %s %s: %s" % (lang, detected_lang, txt))
    return False
  return True

if args.trg_data: # bilingual text
  trg_reader = codecs.getreader('utf8')(open(args.trg_data))
  trg_writer = codecs.getwriter('utf-8')(open("%s.clean.%s" % (args.output_prefix, args.trg_language), "w"))
  while True:
    try:
      src_txt = next(src_reader)
    except StopIteration:
      try:
        next(trg_reader)
        sys.exit("ERROR: target longer than source!!!")
      except StopIteration:
        sys.exit("Source and target have equal length.")
    try:
      trg_txt = next(trg_reader)
    except StopIteration:
      sys.exit("ERROR: source longer than target!!!")
    src_len = len(src_txt.strip().split())
    trg_len = len(trg_txt.strip().split())
    if (check_mono(src_txt.strip(), args.src_language, src_len)
          and check_mono(trg_txt.strip(), args.trg_language, trg_len)):
      if args.max_ratio > 0.0:
        ratio = max(float(src_len)/float(trg_len), float(trg_len)/float(src_len))
        if ratio > args.max_ratio:
          print("HIGH_RATIO %f: %d %d" % (ratio, src_len, trg_len))
          continue
      src_writer.write(src_txt)
      trg_writer.write(trg_txt)
else: # monolingual text
  for src_txt in src_reader:
    src_len = len(src_txt.strip().split())
    if check_mono(src_txt.strip(), args.src_language, src_len):
      src_writer.write(src_txt)


