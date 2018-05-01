'''
This script creates a word level conditional lexical translation probability
table from alignments, e.g. generated with fast_align.
'''
import argparse
import operator

parser = argparse.ArgumentParser(description='Creates a conditional lexical translation '
                            'probability table from word alignments. The probabilities '
                            'are sorted descending, i.e. you can use uniq to get the '
                            'most likely lexical translation.')
parser.add_argument('-a','--align', help='Alignment file (e.g. fast_align format)',
                    required=True)
parser.add_argument('-s','--sentences', help='Corpus file: format <src> ||| <trgt> '
                    'like required by -i parameter of fast_align',
                    required=True)
args = parser.parse_args()

with open(args.align, 'r') as afile:
    with open(args.sentences, 'r') as sfile:
        counts = {}
        sline = sfile.readline()
        while sline:
            src, trgt = [sen.strip().split() 
                               for sen in sline.split(" ||| ", 2)]
            for al in afile.readline().strip().split():
                if not al: # I think its not necessary, but just in case...
                    continue
                src_idx, trgt_idx = al.split('-', 2)
                src_word = src[int(src_idx)]
                trgt_word = trgt[int(trgt_idx)]
                if not src_word in counts:
                    counts[src_word] = {trgt_word: 1}
                elif not trgt_word in counts[src_word]:
                    counts[src_word][trgt_word] = 1
                else:
                    counts[src_word][trgt_word] += 1 
            sline = sfile.readline()
        
        for src_word in counts:
            c = counts[src_word]
            total = sum(c.values()) + 0.0
            for (trgt_word, count) in sorted(c.items(), key=operator.itemgetter(1), reverse=True):
                print("%s %s %f" % (src_word, trgt_word, count/total))
