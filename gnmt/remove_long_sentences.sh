
# Removes sentences with (src_len, trgt_len) >= ($1,$2) from prefix.en and prefix.fr and stores it as prefix.short.en and prefix.short.fr
# Usage: remove_long_sentences.sh <prefix>

prefix="$1"
cat $prefix.en | awk "{if (NF >= $1) print 0; else print 1}" > tmp.valid.en
cat $prefix.fr | awk "{if (NF >= $2) print 0; else print 1}" > tmp.valid.fr

paste -d' ' tmp.valid.en tmp.valid.fr $prefix.en | egrep '^1 1 ' | cut -d' ' -f3- > $prefix.short.en
paste -d' ' tmp.valid.en tmp.valid.fr $prefix.fr | egrep '^1 1 ' | cut -d' ' -f3- > $prefix.short.fr

rm tmp.valid.en tmp.valid.fr
