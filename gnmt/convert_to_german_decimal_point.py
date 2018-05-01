'''
This script tries to find numbers which are formatted with the
dot (.) as decimal point, and replace it with a German style ,
'''
import sys

for line in sys.stdin:
    words = []
    for word in line.strip().split():
        conv_word = word
        # Apply only if word is of the format [number].[number]
        parts = word.split('.')
        if len(parts) == 2 and len(parts[1]) != 3: # !=3 to avoid replacing thousand separator
            try:
                first = int(parts[0])
                second = int(parts[1])
                if (first > 24 or second > 59) and (first > 31 or second > 12): # no date or time
                    conv_word = word.replace('.', ',')
            except Exception:
                pass
        words.append(conv_word)
    print(' '.join(words))

