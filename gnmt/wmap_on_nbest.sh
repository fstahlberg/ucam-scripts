cat $1 | awk -F'|' '{print $4}' | python $(dirname $0)/apply_wmap.py -m $2 -d $3 -t $4 | paste -d'|' - $1 | awk -F'|' '{print $2"||| "$0}' | cut -d'|' -f1-4,9- 

