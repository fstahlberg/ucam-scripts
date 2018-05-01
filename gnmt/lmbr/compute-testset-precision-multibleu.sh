cat /dev/stdin | fgrep 'BLEU = ' | tr '/' ' ' | awk '{print "BLEU: "($4/100)" "($5/100)" "($6/100)" "($7/100)}' | /data/mifs_scratch/fs439/bin/ucam-smt/scripts/lmbr/compute-testset-precisions.pl
