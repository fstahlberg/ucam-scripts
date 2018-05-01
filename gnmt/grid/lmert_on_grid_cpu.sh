#!/bin/bash

source /data/mifs_scratch/fs439/exp/gnmt/scripts/import_hifst_environment15.sh

HELP=false
num_parts=20
iter=5
initial_weights="1.0"
int_refs=data/dev.ids.de
work_dir=./lmert-work
config_file=ini/sgnmt.ini
while [[ $# -gt 0 ]]; do
  case "$1" in
    "--help")
      shift
      HELP=true;
      ;;
    "--num_parts")
      shift;num_parts="$1";shift
      ;;
    "--iter")
      shift;iter="$1";shift
      ;;
    "--initial_weights")
      shift;initial_weights="$1";shift
      ;;
    "--int_refs")
      shift;int_refs="$1";shift
      ;;
    "--work_dir")
      shift;work_dir="$1";shift
      ;;
    "--config_file")
      shift;config_file="$1";shift
      ;;
    *)
      echo "Argument not used: $1"
      shift
  esac
done

if $HELP; then
  echo "This script runs HiFSTs LMERT to optimize predictor weights."
  echo "Parameters:"
  echo "  --help: Print this help text" 
  echo "  --num_parts: Number of parallel grid jobs ($num_parts)" 
  echo "  --iter: Number of iterations ($iter)" 
  echo "  --initial_weights: cf. LMERTs initial_weights. Initial predictor weights, comma separated ($initial_weights)" 
  echo "  --int_refs: cf. LMERTs int_refs. Text file with target sentences ($int_refs)" 
  echo "  --work_dir: Working directory of this script ($work_dir)" 
  echo "  --config_file: SGNMT config file. Must not include predictor_weights or outputs ($config_file)" 
  exit 0
fi

mkdir -p "$work_dir"

weights="$initial_weights"
set_size=$(cat $int_refs | wc -l)
range="1:$set_size"
decode_script=$(dirname $0)/decode_on_grid_cpu.sh

for i in $(seq $iter)
do
  echo "ITERATION $i"
  iter_dir=$work_dir/$i
  mkdir $iter_dir
  echo $weights > $iter_dir/weights.txt
  export TUPLEARC_WEIGHT_VECTOR=$weights
 
  # Create config file
  cp $config_file $iter_dir/config.ini
  echo "predictor_weights: $weights" >>  $iter_dir/config.ini
  echo "outputs: text,fst,nbest" >>  $iter_dir/config.ini

  # Run decoder
  cmd="$decode_script $num_parts $range $iter_dir/config.ini $iter_dir"
  echo "DECODE CMD:$cmd"
  eval $cmd

  # Wait
  while [ ! -f $iter_dir/DONE ]
  do
    echo $(date)": Waiting for $iter_dir/DONE..."
    sleep 30
  done

  # Combine previous lattices with new lattices
  mkdir $iter_dir/out.fst.all
  if [ ! -z $prev_dir ]
  then
    for idx in $(seq $set_size)
    do
      TUPLEARC_WEIGHT_VECTOR=$weights fstunion $prev_dir/$idx.fst $iter_dir/out.fst/$idx.fst | fstrmepsilon | fstdeterminize | fstminimize > $iter_dir/out.fst.all/$idx.fst
    done
  else
    for idx in $(seq $set_size)
    do
      TUPLEARC_WEIGHT_VECTOR=$weights fstrmepsilon $iter_dir/out.fst/$idx.fst | fstdeterminize | fstminimize > $iter_dir/out.fst.all/$idx.fst
    done
  fi

  # Run LMERT
  prev_dir=$iter_dir/out.fst.all
  cmd="TUPLEARC_WEIGHT_VECTOR=$weights lmert.O2.bin --range=$range --input=$iter_dir/out.fst.all/?.fst --initial_params=$weights --int_refs=$int_refs --write_params $iter_dir/weights.opt.txt"
  echo "LMERT CMD: $cmd"
  eval $cmd

  # Shift weights in case of negative lambdas
  #offset=$(cat $iter_dir/weights.opt.txt | tr ',' "\n" | awk 'BEGIN{m=0}{if ($1<m) m=$1}END{print m}')
  offset=0
  weights=$(cat $iter_dir/weights.opt.txt | tr ',' "\n" | awk '{print '$offset'*-1+$1}' | tr "\n" ',' | sed 's/,$//')
done

echo "FINAL WEIGHTS: $weights"
export TUPLEARC_WEIGHT_VECTOR=""
