#!/bin/bash
# A small script which cleans up a SGNMT output directory:
# It deletes all the worker directories
# It deletes all log files and replace them with log.info which
# only contains INFO log messages
# Change into the output directory and execute this script

for exp_dir in */
do
  cd $exp_dir
  echo "Change to $exp_dir"
  rm -r $(ls | egrep '^[0-9]+$')
  cat logs/* | fgrep INFO > log.info
  rm logs/*
  mv log.info logs
  cd ..
done 
