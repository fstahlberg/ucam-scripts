#!/bin/bash
#$ -S /bin/bash

# check version of ubuntu
release=`lsb_release -s -d`
v12=`echo $release | grep 12.04`
v14=`echo $release | grep 14.04`

hostname=`hostname`
has_gpu=`echo $hostname | grep air2`

if [ ! -z $has_gpu ]; then
    if [ -z $X_SGE_CUDA_DEVICE ]; then X_SGE_CUDA_DEVICE=0; fi
    export CUDA_VISIBLE_DEVICES=$X_SGE_CUDA_DEVICE  # only the specified GPU is usable
    device="gpu:$X_SGE_CUDA_DEVICE"

    echo "hostname="$hostname" running $release"
    echo "X_SGE_CUDA_DEVICE="$X_SGE_CUDA_DEVICE
    if [ ! -z "$v12" ]; then
	export PATH="/home/mifs/ech57/tools/anaconda/bin/:/home/mifs/ech57/tools/bazel-0.2.2b/output/:$PATH"
	export LD_LIBRARY_PATH=/usr/local/cuda-7.0/lib64/:/home/mifs/ech57/tools/cudnn-7.0-linux-x64-v4.0-prod/lib64/
	
	source activate tensorflow_12.04
	tensorflow=/home/mifs/ech57/code/tensorflow_12.04
    elif [ ! -z "$v14" ]; then
	export PATH="/home/mifs/ech57/tools/anaconda/bin/:/home/mifs/ech57/tools/bazel-0.2.2b/output/:/home/mifs/fs439/bin/gcc/gcc-4.9.3/bin/:$PATH"
	export LD_LIBRARY_PATH=/usr/local/cuda-7.0/lib64/:/home/mifs/ech57/tools/cudnn-7.0-linux-x64-v4.0-prod/lib64/:/home/mifs/fs439/bin/gcc/gcc-4.9.3/lib64/
	source activate tensorflow
	tensorflow=/home/mifs/ech57/code/tensorflow
    fi
else
    device="cpu:0"

    echo "hostname="$hostname" running $release"
    if [ ! -z "$v12" ]; then
        export PATH="/home/mifs/ech57/tools/anaconda/bin/:/home/mifs/ech57/tools/bazel-0.2.2b/output/:/home/mifs/fs439/bin/gcc/gcc-4.9.3/bin/:$PATH"
        export LD_LIBRARY_PATH=/home/mifs/fs439/bin/gcc/gcc-4.9.3/lib64/

        source activate tensorflow_cpu_12.04
	tensorflow=/home/mifs/ech57/code/tensorflow_cpu_12.04
    elif [ ! -z "$v14" ]; then
        export PATH="/home/mifs/ech57/tools/anaconda/bin/:/home/mifs/ech57/tools/bazel-0.2.2b/output/:$PATH"
        source activate tensorflow_cpu
        tensorflow=/home/mifs/ech57/code/tensorflow_cpu
    fi
fi


source /home/mifs/ech57/exps/tensorflow/scripts/import_hifst_environment15.sh

# pywrapfst, nplm, srilm
export PYTHONPATH=/data/mifs_scratch/fs439/bin/ucam-smt/externals/openfst-1.5.2/INSTALL_DIR/lib/python2.7/site-packages:/home/mifs/fs439/bin/nplm-0.3/python/:/home/mifs/fs439/bin/swig-srilm/:$PYTHONPATH
export OMP_NUM_THREADS=1
