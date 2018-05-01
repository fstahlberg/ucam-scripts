#!/bin/sh
#
# the next line is a "magic" comment that tells gridengine to use bash
#$ -S /bin/bash
#
# and now for some real work


if [ $# -ne 3 ] ; then
  echo "Usage: ./length_norm_nbest.sh <src-sens> <moses-nbest> <out_directory>"
  echo "  Normalize scores in a nbest list by sentence length using GNMT."
  echo "    <src-sens>: Source sentences (indexed). See GNMT's --src_test"
  echo "    <moses-nbest>: nbest list in Moses format"
  echo "    <out_directory>: Output directory. Will create out.text, out.nbest, and out.sfst"
  exit 1;
fi

export LC_ALL=en_GB.utf8
# Override some of the settings automatically set by grid
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games"
export LD_LIBRARY_PATH=/home/mifs/ech57/tools/BLAS:/home/mifs/fs439/bin/nplm-0.3/src/python:/home/mifs/fs439/bin/gcc/gcc-4.9.3/lib64:/home/mifs/fs439/bin/openfst-1.5.0/bin/lib/
export PYTHONPATH=/home/mifs/fs439/bin/nplm-0.3/python/
export THEANO_FLAGS="on_unused_input='warn',base_compiledir=/data/mifs_scratch/fs439/sys-tmp/theano_cpu,device=cpu,blas.ldflags=-lblas -lgfortran"

echo "Theano flags: "$THEANO_FLAGS
echo "PATH="$PATH
echo "LD_LIBRARY_PATH="$LD_LIBRARY_PATH
echo "PYTHONPATH="$PYTHONPATH

src=$1
nbest=$2
out=$3

mkdir -p $out
python /home/mifs/fs439/bin/gnmt/decode.py --combination_scheme length_norm --decoder dfs --early_stopping false --src_test $src --trg_test $nbest --predictors forcedlst --use_nbest_weights true --outputs text,nbest,sfst --output_path $out/out.%s 

