qstat | fgrep '@' | cut -d'@' -f2- | cut -d'.'  -f1 | sort -u | tr "\n" ',' | xargs qhost -h
