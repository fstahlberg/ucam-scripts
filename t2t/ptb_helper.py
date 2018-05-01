# coding=utf-8

import re

penn_escape_map = [
  ("(", "-LRB-"), 
  (")", "-RRB-"), 
  ("[", "-LSB-"), 
  ("]", "-RSB-"), 
  ("{", "-LCB-"), 
  ("}", "-RCB-"),
  ("&amp;", "&"),
  ("–", "--"),
  ("—", "--"),
  ("\xc2\xad", "-"),
  ("\"", "''"),
  ("“", "``"),
  ("”", "''"),
  ("‘", "`"),
  ("’", "'"),
  ("«", "``"),
  ("»", "''"),
  ("‹", "`"),
  ("›", "'"),
  ("„", "``"),
  ("”", "''"),
  ("‚", "`"),
  ("’", "'"),
  ("€", "$"),
  ("\u00A2", "$"),
  ("\u00A3", "$"),
  ("\u00A4", "$"),
  ("\u00A5", "$"),
  ("\u0080", "$"),
  ("\u20A0", "$"),
  ("\u20AA", "$"),
  ("\u20AC", "$"),
  ("\u20B9", "$"),
  ("\u060B", "$"),
  ("\u0E3F", "$"),
  ("\u20A4", "$"),
  ("\uFFE0", "$"),
  ("\uFFE1", "$"),
  ("\uFFE5", "$"),
  ("\uFFE6", "$")
]

penn_unescape_map = [
  ("(", "-LRB-"), 
  (")", "-RRB-"), 
  ("[", "-LSB-"), 
  ("]", "-RSB-"), 
  ("{", "-LCB-"), 
  ("}", "-RCB-"),
  ("\"", "''"),
  ("\"", "``"),
  ("'", "`")
]

# The simple Tokenizer replaces brackets and quotes
class SimpleTokenizer(object):
    def tokenize(self, text):
        for raw, ptb in penn_escape_map:
          text = text.replace(raw, ptb)
        return text

class SimpleDetokenizer(object):
    def detokenize(self, text):
        for raw, ptb in penn_unescape_map:
          text = text.replace(ptb, raw)
        return text
    


# The PTB Tokenizer has been copied from
# http://www.nltk.org/_modules/nltk/tokenize/treebank.html
class MacIntyreContractions:
    CONTRACTIONS2 = [r"(?i)\b(can)(?#X)(not)\b",
                     r"(?i)\b(d)(?#X)('ye)\b",
                     r"(?i)\b(gim)(?#X)(me)\b",
                     r"(?i)\b(gon)(?#X)(na)\b",
                     r"(?i)\b(got)(?#X)(ta)\b",
                     r"(?i)\b(lem)(?#X)(me)\b",
                     r"(?i)\b(mor)(?#X)('n)\b",
                     r"(?i)\b(wan)(?#X)(na)\s"]
    CONTRACTIONS3 = [r"(?i) ('t)(?#X)(is)\b", r"(?i) ('t)(?#X)(was)\b"]
    CONTRACTIONS4 = [r"(?i)\b(whad)(dd)(ya)\b",
                     r"(?i)\b(wha)(t)(cha)\b"]


class TreebankWordTokenizer(object):
    #starting quotes
    STARTING_QUOTES = [
        (re.compile(r'^\"'), r'``'),
        (re.compile(r'(``)'), r' \1 '),
        (re.compile(r'([ (\[{<])"'), r'\1 `` '),
    ]

    #punctuation
    PUNCTUATION = [
        (re.compile(r'([:,])([^\d])'), r' \1 \2'),
        (re.compile(r'([:,])$'), r' \1 '),
        (re.compile(r'\.\.\.'), r' ... '),
        (re.compile(r'[;@#$%&]'), r' \g<0> '),
        (re.compile(r'([^\.])(\.)([\]\)}>"\']*)\s*$'), r'\1 \2\3 '), # Handles the final period.
        (re.compile(r'[?!]'), r' \g<0> '),

        (re.compile(r"([^'])' "), r"\1 ' "),
    ]

    # Pads parentheses
    PARENS_BRACKETS = (re.compile(r'[\]\[\(\)\{\}\<\>]'), r' \g<0> ')

    # Optionally: Convert parentheses, brackets and converts them to PTB symbols.
    CONVERT_PARENTHESES = [
        (re.compile(r'\('), '-LRB-'), (re.compile(r'\)'), '-RRB-'),
        (re.compile(r'\['), '-LSB-'), (re.compile(r'\]'), '-RSB-'),
        (re.compile(r'\{'), '-LCB-'), (re.compile(r'\}'), '-RCB-')
    ]

    DOUBLE_DASHES = (re.compile(r'--'), r' -- ')

    #ending quotes
    ENDING_QUOTES = [
        (re.compile(r'"'), " '' "),
        (re.compile(r'(\S)(\'\')'), r'\1 \2 '),
        (re.compile(r"([^' ])('[sS]|'[mM]|'[dD]|') "), r"\1 \2 "),
        (re.compile(r"([^' ])('ll|'LL|'re|'RE|'ve|'VE|n't|N'T) "), r"\1 \2 "),
    ]

    # List of contractions adapted from Robert MacIntyre's tokenizer.
    _contractions = MacIntyreContractions()
    CONTRACTIONS2 = list(map(re.compile, _contractions.CONTRACTIONS2))
    CONTRACTIONS3 = list(map(re.compile, _contractions.CONTRACTIONS3))

    def tokenize(self, text, convert_parentheses=True, return_str=True):
        for regexp, substitution in self.STARTING_QUOTES:
            text = regexp.sub(substitution, text)

        for regexp, substitution in self.PUNCTUATION:
            text = regexp.sub(substitution, text)

        # Handles parentheses.
        regexp, substitution = self.PARENS_BRACKETS
        text = regexp.sub(substitution, text)
        # Optionally convert parentheses
        if convert_parentheses:
            for regexp, substitution in self.CONVERT_PARENTHESES:
                text = regexp.sub(substitution, text)

        # Handles double dash.
        regexp, substitution = self.DOUBLE_DASHES
        text = regexp.sub(substitution, text)

        #add extra space to make things easier
        text = " " + text + " "

        for regexp, substitution in self.ENDING_QUOTES:
            text = regexp.sub(substitution, text)

        for regexp in self.CONTRACTIONS2:
            text = regexp.sub(r' \1 \2 ', text)
        for regexp in self.CONTRACTIONS3:
            text = regexp.sub(r' \1 \2 ', text)

        # We are not using CONTRACTIONS4 since
        # they are also commented out in the SED scripts
        # for regexp in self._contractions.CONTRACTIONS4:
        #     text = regexp.sub(r' \1 \2 \3 ', text)

        return text if return_str else text.split()

def clean_up_linearization(linear):
  """Fixes common problems with noisy output when passed to evalb."""
  # punctuation and quotes as non-terminals cause problems in evalb
  linear = re.sub(r"\([.,`']+ ([^)]*[^.,`')][^)]*)\)", r"(<dummy> \1)", linear) 
  linear = re.sub(r"\([.,`']+ ('[a-z])", r"(<dummy> \1", linear) 
  linear = re.sub(r"\(: ([^;:-])", r"(<dummy> \1", linear) 
  # Wrongly labelled punctuation and quotes cause problems downstream in evalb
  linear = re.sub(r"\([^., ]+ ([.,]+)\)", r"(\1 \1)", linear) 
  linear = re.sub(r"\([^ ]+ ([.,]{2,})\)", r"(: \1)", linear)
  linear = re.sub(r"\([^`' ]+ ([`']+)\)", r"('' \1)", linear) 
  linear = re.sub(r"\(([`']) ([`']+)\)", r"(\1\1 \2)", linear) 
  linear = re.sub(r"\([^: ]+ ([;:-]+)\)", r"(: \1)", linear) 
  linear = re.sub(r"\([^. ]+ ([!?]+)\)", r"(. \1)", linear) 
  linear = re.sub(r"\([^ ]+ -([RL])([A-Z]B)\)", r"(-\1RB -\1\2)", linear) 
  # Collapse (foo (<uni|dummy> bar)) into (foo bar)
  linear = re.sub(r"\(([^ ]+) \(<[^ ]+> ([^)]+)\)\)", r"(\1 \2)", linear)
  # Artefacts like '(terminal)' ocassionally pop up in the output
  linear = re.sub(r"\(([^ ()]+)\)", r"(\1 \1)", linear) 
  # Artefacts like ') terminal)' 
  linear = re.sub(r"\) ([^ ()]+)\)", r") (\1 \1))", linear)
  linear = linear.strip()
  return linear

