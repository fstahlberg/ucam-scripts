#!/usr/bin/env bash
#
# NOTE: Adaptation from lexparser-lang.sh 
#
# Defines standard configurations for parsing with the
# multilingual parsers (Arabic, Chinese, German, French). 
#
# For English, it is easier to use lexparser.sh, although you can load 
# an English grammar with this script.
#
# For details on the language-specific options, see the javadocs and
# lexparser_lang.def.
#

# Memory limit
mem=7g

if [ ! $# -ge 1 ]; then
   echo Usage: `basename $0` lang FILE...
   echo
   echo '  lang       : Language to parse (Arabic, English, Chinese, German, French)'
   echo '  FILE       : List of files to parse'
   echo
   echo 'To set additional parser options, modify parse_opts in lexparser_lang.def'
   echo 
   echo 'Parser memory limit is currently:' "$mem"
   echo   
   echo 'Produces FILE.penn with human readable parse trees.'
   echo   
   exit
fi

# Setup command-line options
lang=$1

shift 1

# Language-specific configuration
scriptdir=/data/mifs_scratch/fs439/bin/stanford-parser
source $scriptdir/lexparser_lang.def

# Setting classpath
CLASSPATH="$CLASSPATH":"$scriptdir/*"

# Select grammar
if [ "$lang" = "English" ]
then
  grammar=edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz
fi
if [ "$lang" = "German" ]
then
  grammar=edu/stanford/nlp/models/lexparser/germanFactored.ser.gz
fi
if [ "$lang" = "Chinese" ]
then
  grammar=edu/stanford/nlp/models/lexparser/chineseFactored.ser.gz
fi

# Run the Stanford parser
echo "Using grammar '$grammar'"
/home/mifs/fs439/bin/jdk1.8.0_65/bin/java -Xmx"$mem" -cp "$CLASSPATH" edu.stanford.nlp.parser.lexparser.LexicalizedParser \
  -tLPP "$tlp" $lang_opts $parse_opts -writeOutputFiles \
  -outputFormatOptions "includePunctuationDependencies" \
  -outputFilesExtension penn -outputFormat "penn" -encoding UTF-8 \
  -sentences newline -maxLength 150 -loadFromSerializedFile $grammar $*
# -nthreads 1

# Postprocess
for f in $*
do
  cat $f.penn | egrep -v '^[ ()]+$' | tr -d "\n" | sed "s/(ROOT /\n(ROOT /g" | sed 's/ *$//' | sed 's/ \+/ /g' | sed 's/^ *//' | tail -n +2 > $f.penn.compact
  echo '' >> $f.penn.compact
done
