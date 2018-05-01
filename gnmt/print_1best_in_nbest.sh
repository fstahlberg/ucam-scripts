#!/bin/bash
uniq -w 5 | cut -d'|' -f4 | sed 's/^ *//' | sed 's/ *$//' <&0
