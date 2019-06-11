cat /dev/stdin | fstprint  | awk '{if (NF ==5) {$5 *= '$1'} print $0}' | fstcompile
