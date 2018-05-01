#!/bin/bash

export LC_ALL=en_GB.utf8

cat /dev/stdin | python /data/mifs_scratch/fs439/exp/gnmt/scripts/apply_wmap.py -m /data/mifs_scratch/fs439/exp/t2t/enzh/data/wmap.bpe.en -t eow -d i2s | /data/mifs_scratch/fs439/bin/moses/scripts/recaser/detruecase.perl | /data/mifs_scratch/fs439/bin/moses/scripts/tokenizer/detokenizer.perl -l en > tmp.bleu.hyp
cat tmp.bleu.hyp | perl /home/mifs/ech57/tools/mosesdecoder/scripts/ems/support/wrap-xml.perl en /data/mifs_scratch/fs439/exp/t2t/wmt_sgm/references/newstest2017-zhen-src.zh.sgm UCAM > tmp.bleu.sgm

/data/mifs_scratch/fs439/bin/moses/scripts/generic/mteval-v13a.pl -c -s /data/mifs_scratch/fs439/exp/t2t/wmt_sgm/references/newstest2017-zhen-src.zh.sgm -r /data/mifs_scratch/fs439/exp/t2t/wmt_sgm/references/newstest2017-zhen-ref.en.sgm  -t tmp.bleu.sgm -d 3 > tmp.bleu.eval

cat tmp.bleu.eval | tr "\n" ' ' | sed 's/Cumulative.*$//' | sed 's/^.*length ratio: \([0-9.-]\+\) (\([0-9.-]\+\)\/\([0-9.-]\+\)), penalty (log): \([0-9.-]\+\).*BLEU score = \([0-9.-]\+\) .*BLEU:/\1 \2 \3 \4 \5/' | awk '{print "BLEU = "($5*100)", "($6*100)"/"($7*100)"/"($8*100)"/"($9*100)" (BP="exp($4)", ratio="$1", hyp_len="$2", ref_len="$3")"}'


