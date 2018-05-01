#!/bin/bash

HELP=false
SHOW_WEIGHTS=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    "-help")
      shift
      HELP=true;
      ;;
    "-show-weights")
      shift
      SHOW_WEIGHTS=true;
      ;;
    "-weight-overwrite")
      shift;weight_param="$1";shift
      ;;
    "-initial-weights")
      shift;initial_weights="$1";shift
      ;;
    "-gnmt-pid")
      shift;gnmt_pid="$1";shift
      ;;
    "-predictors")
      shift;predictors="$1";shift
      ;;
    "-n-best-list")
      shift;nbest_path=$1;shift;nbest=$1;shift
      ;;
    "-input-file")
      shift;input_file="$1";shift
      ;;
    *)
      echo "Argument not used: $1"
      shift
  esac
done

if $HELP; then
  echo "This script simulates the moses decoder but runs GNMT in the background"
  echo "This is helpful for MERT training with moses-mert.pl"
  echo "Parameters:"
  echo "  -help: Print this help text" 
  echo "  -show-weights: Print initial predictor weights (uniform)" 
  echo "  -weight-overwrite: Predictor weights 'nmt= 0.2 fst= 0.5 ...'" 
  echo "  -initial-weights: Initial predictor weights shown with -show-weights, comma separated" 
  echo "  -gnmt-pid: Process ID of GNMT process in interactive/stdin mode" 
  echo "  -predictors: Predictor parameter of the GNMT process" 
  echo "  -n-best-list <path> <n>: Path to the nbest file to generate" 
  echo "  -input-file: Input file (indexed)" 
  exit 0
fi

if $SHOW_WEIGHTS; then
  if [ -z $initial_weights ]; then
    uni_weight=$(echo $predictors | awk -F',' '{print 1/NF}')
    echo $predictors | tr ',' "\n" | sed 's/_/0/g' | sed "s/^.*$/\0= $uni_weight/"
  else
    i=1
    for pred in $(echo $predictors | tr ',' "\n")
    do
      echo $(echo $pred | tr '_' '0')"= "$(echo $initial_weights | tr ',' "\n" | awk '{if (NR=='$i') print $0}')
      i=$(echo "1+$i" | bc)
    done
  fi
  exit 0
fi

echo "FAKE MOSES CONFIG:"
echo "weight-overwrite -> $weight_param"
echo "gnmt_pid -> $gnmt_pid"
echo "predictors -> $predictors"
echo "nbest_path -> $nbest_path"
echo "nbest -> $nbest"
echo "input_file -> $input_file"

for pred in $(echo "$predictors" | tr ',' "\n")
do
    pred_weights="$pred_weights,"$(echo $weight_param | egrep -io $(echo $pred | sed 's/_/0/')" *= *([-.e+0-9]+)" | cut -d'=' -f2 | sed 's/^ *//')
done
pred_weights=${pred_weights:1}
echo "predator_weights -> $pred_weights"

rm $nbest_path

echo "SET WEIGHTS TO $pred_weights AND RESET"

cmd="!gnmt config beam $nbest"
echo "GNMT-CMD:$cmd"
echo $cmd > /proc/$gnmt_pid/fd/0

cmd="!gnmt config nbest $nbest"
echo "GNMT-CMD:$cmd"
echo $cmd > /proc/$gnmt_pid/fd/0

cmd="!gnmt config outputs nbest"
echo "GNMT-CMD:$cmd"
echo $cmd > /proc/$gnmt_pid/fd/0

cmd="!gnmt config output_path mert-work/$nbest_path"
echo "GNMT-CMD:$cmd"
echo $cmd > /proc/$gnmt_pid/fd/0

cmd="!gnmt config predictor_weights $pred_weights"
echo "GNMT-CMD:$cmd"
echo $cmd > /proc/$gnmt_pid/fd/0

cmd="!gnmt reset"
echo "GNMT-CMD:$cmd"
echo $cmd > /proc/$gnmt_pid/fd/0

cmd="!gnmt decode $input_file"
echo "GNMT-CMD:$cmd"
echo $cmd > /proc/$gnmt_pid/fd/0



while [ ! -f "$nbest_path" ];
do
  sleep 6
  echo $(date)" and still decoding..."
done
sleep 15

echo "Written to $nbest_path"
