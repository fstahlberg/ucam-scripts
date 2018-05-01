'''
This script is an extension of lowercase_except_oovs.py and handles casing
when the [HiFST] system was trained on a lower cased source side. We could just
lower case everything, but this would lead to incorrectly cased pass-through
rules. lowercase_except_oovs.py fixes this by lower casing all words except OOVs.

However, this still can cause issues with surnames, e.g. Orlando Bloom, or Dawn,
which are not OOV when they are lower cased. This script aims to tackle this by
only lower-casing non-OOVs if they occurred in the true-cased training corpus
with this casing. This still does not fix all issues: If Orlando Bloom also
occurrs in the training corpus, we still could end up translating his surname.

Another twist of this script is that it tries to recognize headings in which
all words start upper cased. In this case, we fall back to the policy of
lowercase_except_oovs.py
 
Use this script if source side is trained lower-cased to create correctly
cased OOV pass through rules
'''

import logging
import argparse
import sys

def load_wmap(path, inverse=False, lc=False):
    with open(path) as f:
        if lc:
            d = dict(line.lower().strip().split(None, 1) for line in f)
        else:
            d = dict(line.strip().split(None, 1) for line in f)
        if inverse:
            d = dict(zip(d.values(), d.keys()))
        return d

parser = argparse.ArgumentParser(description='Transform true cased input at stdin to for feeding it to '
                                 'a lower cased MT system. This means lower casing most of the time except '
                                 'for some exceptions (read source of this script)'
                                 'Usage: python case_for_lc_system.py -m wmap.en < in_sens > out_sens')
parser.add_argument('-c','--cased_vocab', help='Word map which defines the set of words which retain casing even if they are in recog_vocab (format: see -i parameter)',
                    required=True)
parser.add_argument('-r','--recog_vocab', help='Word map which defines the vocabulary of the recognizer (format: see -i parameter)',
                    required=True)
parser.add_argument('-n','--number_vocab', help='Word map which defines the true cased frequencies of words (format: see -i parameter)',
                    required=True)
parser.add_argument('-i','--inverse_wmap', help='Use this argument to use word maps with format "id word".'
                    ' Otherwise the format "word id" is assumed', action='store_true')
args = parser.parse_args()

cased_wmap = load_wmap(args.cased_vocab, args.inverse_wmap, True)
recog_wmap = load_wmap(args.recog_vocab, args.inverse_wmap, True)
counts_wmap = load_wmap(args.number_vocab, args.inverse_wmap)

def is_upper_cased_heading(line):
    # Note: Imbalanced risk: Failing to recognize a upper cased heading is much worse
    # than classifiying a normal line as upper cased heading. Therefore, use a low threshold
    words = line.strip().split()
    return (0.0 + len([w for w in words if w != w.lower()])) / len(words) > 0.4

for line in sys.stdin:
    if is_upper_cased_heading(line): # fall back to lowercase_except_oovs.py policy
        print(' '.join([w.lower() if w.lower() in recog_wmap else w for w in line.strip().split()]))
    else: # if OOV and not in tc_wmap with this casing, keep casing. Otherwise lower case
        words = []
        for w in line.strip().split():
            lc_w = w.lower()
            if lc_w == w or not lc_w in recog_wmap: # OOVs and words which are already lc
                words.append(w)
            elif not lc_w in cased_wmap: # Not in the short list
                words.append(lc_w)
            elif len(w) > 0 and lc_w != w[0].lower() + w[1:]: # lc if casing is more complex as first char only
                words.append(lc_w)
            elif int(counts_wmap.get(w,'0')) > 5: # If this casing occurs frequently in training corpus, trust translation model
                words.append(lc_w)
            elif int(counts_wmap.get(w,'0')) + int(counts_wmap.get(w,'0')) > 300: # Seems to be a common word as part of a proper name -> lower case
                words.append(lc_w)
            else:
                words.append(w)
        print(' '.join(words))
