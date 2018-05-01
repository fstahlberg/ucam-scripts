'''
This script replaces all word ids larger than a certain value with UNK
'''

import logging
import argparse
import sys

parser = argparse.ArgumentParser(description='Replace all word ids in stdin greater than voc size with unk')
parser.add_argument('-v','--voc_size', default=30003, help='Vocabulary size', required=False)
parser.add_argument('-u','--unk_id', default='0', help='UNK id', required=False)
args = parser.parse_args()

unk_id = args.unk_id
voc_size = int(args.voc_size)

for line in sys.stdin:
    print(' '.join([unk_id if int(w) >= voc_size else w for w in line.strip().split()]))
