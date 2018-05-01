cat /dev/stdin | awk '{for(i=NF;i>=1;i--) printf "%s ", $i;print ""}' | sed 's/* $//' 
