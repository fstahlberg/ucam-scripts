
# hifst see http://ucam-smt.github.io/tutorial/build.html
export HiFSTROOT=/data/mifs_scratch/fs439/bin/ucam-smt-20170804/
source $HiFSTROOT/Makefile.inc
export PATH=$HiFSTROOT/bin:$OPENFST_BIN:$PATH
export LD_LIBRARY_PATH=$HiFSTROOT/bin:$OPENFST_LIB:$BOOST_LIB:$LD_LIBRARY_PATH

# sgnmt see http://ucam-smt.github.io/sgnmt/html/setup.html
export LD_LIBRARY_PATH=/home/mifs/fs439/bin/nplm-0.3/src/python:/home/mifs/fs439/bin/swig-srilm/:$LD_LIBRARY_PATH
export PYTHONPATH=/data/mifs_scratch/fs439/bin/anaconda2/lib/python2.7/site-packages:$OPENFST_LIB/python2.7/site-packages/:/home/mifs/fs439/bin/swig-srilm/:/home/mifs/fs439/bin/nplm-0.3/python/:$PYTHONPATH
export SGNMT=/home/mifs/fs439/bin/sgnmt/

# cuda
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:/home/mifs/fs439/bin/gcc/gcc-4.9.3/lib64:$LD_LIBRARY_PATH
export PATH=/usr/local/cuda/bin:$PATH

# Theano flags (for CPU)
export THEANO_FLAGS="on_unused_input='ignore',device=cpu"

