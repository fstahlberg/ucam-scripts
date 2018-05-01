cat /dev/stdin |  /data/mifs_scratch/fs439/exp/t2t/scripts/reverse_words.sh | sed 's/: *1 /: 2 /' | sed 's/ 2 *$/ 1/' | awk -F':' '{print $2": "$1}' | sed 's/^ *//' | sed 's/ *$//' 


