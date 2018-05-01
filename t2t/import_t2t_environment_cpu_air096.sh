# Source this file to set up T2T + SGNMT in grid environment for CPU-only

export PATH=/data/mifs_scratch/fs439/bin/tf_anaconda_cpu_air096/bin:$PATH
source activate tensorflow_cpu_air096
export PYTHONPATH=/home/mifs/fs439/bin/tensor2tensor-usr
export LC_ALL=en_GB.utf8
USR_DIR=/home/mifs/fs439/bin/tensor2tensor-usr/
DATA_DIR=$(pwd)/t2t_data

# HiFST
export HiFSTROOT=/data/mifs_scratch/fs439/bin/ucam-smt-20170804/
source $HiFSTROOT/Makefile.inc
export PATH=$HiFSTROOT/bin:$OPENFST_BIN:$PATH
export LD_LIBRARY_PATH=$HiFSTROOT/bin:$OPENFST_LIB:$BOOST_LIB:$LD_LIBRARY_PATH
export PYTHONPATH=$OPENFST_LIB/python2.7/site-packages/:$PYTHONPATH

# NPLM
#export LD_LIBRARY_PATH=/home/mifs/fs439/bin/nplm-0.3/src/python:$LD_LIBRARY_PATH
#export PYTHONPATH=/home/mifs/fs439/bin/nplm-0.3/python/:$PYTHONPATH

# SRILM
#export LD_LIBRARY_PATH=/home/mifs/fs439/bin/swig-srilm/:$LD_LIBRARY_PATH
#export PYTHONPATH=/home/mifs/fs439/bin/swig-srilm/:$PYTHONPATH

# SGNMT
export SGNMT=/home/mifs/fs439/bin/sgnmt/

# Ubuntu 12.04
export PATH=/data/mifs_scratch/fs439/bin/bazel-0.5.4/bin:/home/mifs/fs439/bin/gcc/gcc-4.9.3/bin/:$PATH
export LD_LIBRARY_PATH=/home/mifs/fs439/bin/gcc/gcc-4.9.3/lib64:$LD_LIBRARY_PATH
