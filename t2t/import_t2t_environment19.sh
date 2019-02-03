# Source this file to set up T2T + SGNMT in grid environment

# Unsetting LD_PRELOAD prevents seg faults when submitted with SGE
unset LD_PRELOAD

export PATH=/data/mifs_scratch/fs439/bin/tf_anaconda19/bin:$PATH
source activate tensorflow19
source /home/mifs/fs439/bin/cuda-9.0_cudnn-7.1/activate.sh 
export PYTHONPATH=/home/mifs/fs439/bin/tensor2tensor-usr
export LC_ALL=en_GB.utf8
if [ ! -z "$X_SGE_CUDA_DEVICE" ];
then
  echo "Set CUDA_VISIBLE_DEVICES to $X_SGE_CUDA_DEVICE"
  export CUDA_VISIBLE_DEVICES=$X_SGE_CUDA_DEVICE
fi
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

# Nizza
export PYTHONPATH=/home/mifs/fs439/bin/nizza/:$PYTHONPATH

# SGNMT MoE
export PYTHONPATH=/home/mifs/fs439/bin/sgnmt_moe/:$PYTHONPATH

# SGNMT
export SGNMT=/home/mifs/fs439/bin/sgnmt/
