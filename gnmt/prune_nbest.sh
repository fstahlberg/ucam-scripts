cat /dev/stdin | sed 's/^\([0-9]\+\) *|||/\1|||/' | awk -F'|' 'BEGIN{cur_id=-1;n=1}{if ($1 == cur_id && n < '$1') { print $0 } else if ($1 != cur_id) { print $0; cur_id = $1; n = 0; } n++}'
