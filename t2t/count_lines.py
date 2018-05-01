# coding=utf-8
r"""Count the number of lines, mainly to address issues like

https://stackoverflow.com/questions/17273598/python-codecs-line-ending
"""

import sys, traceback
import argparse
import codecs

parser = argparse.ArgumentParser(description='Count the number of lines using Python.')
parser.add_argument('-i','--input_file', help='Input file')
args = parser.parse_args()

utf8_reader = codecs.getreader('utf8')(open(args.input_file, 'r'))
codecs_reader = codecs.open(args.input_file, 'r', 'utf8')
byte_reader = open(args.input_file, 'r')

def print_lines(name, reader):
  try:
    n = 0
    for s in reader:
      n += 1
      #print(ord(s[-1:]))
    print("line count: %d (%s)" % (n, name))
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_exception(exc_type, exc_value, exc_traceback,
                              limit=2, file=sys.stdout)


print(args.input_file)
print_lines("UTF-8", utf8_reader)
print_lines("codecs", codecs_reader)
print_lines("byte", byte_reader)


