#!/bin/bash

while read line
do
    echo "$line" | sed 's/[«»]/\&quot;/g' | sed 's/ *’/\&apos;/g'
done < "${1:-/dev/stdin}"

