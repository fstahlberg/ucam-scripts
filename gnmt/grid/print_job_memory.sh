qstat -j $1 | fgrep usage  | sed 's/^usage *\([0-9]\+\).*vmem=\([^,]\+\), max.*$/\1 \2/' | sort -k2 -h
