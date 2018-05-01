cat $1 | cut -d'|' -f4,10 | tr -d '|' | awk '{if (NF>1) print $NF/(NF-1); else print $1}' | paste -d' ' - $1 | awk '{$NF=$1; print $0}' | sort -g -k1 -r | sort -s -g -k2 | cut -d' ' -f2-
