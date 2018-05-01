#!/bin/bash

HELP=false
work_dir=./lmert-work
lmert_bin=/data/smt2016/aaw35/tools/latmert.v1.8/scripts/latmert
n_iter=5
num_parts=20
src=data/dev.ids.en
trg=data/dev.ids.fr
while [[ $# -gt 0 ]]; do
  case "$1" in
    "-help")
      shift
      HELP=true;
      ;;
    "-num-parts")
      shift;num_parts="$1";shift
      ;;
    "-src")
      shift;src="$1";shift
      ;;
    "-ref")
      shift;ref="$1";shift
      ;;
    "-lmert-pipe")
      shift;pipe="$1";shift
      ;;
    "-iter")
      shift;n_iter="$1";shift
      ;;
    "-initial-weights")
      shift;initial_weights="$1";shift
      ;;
    "-lmert-bin")
      shift;lmert_bin="$1";shift
      ;;
    "-lmert-args")
      shift;lmert_args="$1";shift
      ;;
    "-work-dir")
      shift;work_dir="$1";shift
      ;;
    "-gnmt-config-file")
      shift;gnmt_config_file="$1";shift
      ;;
    *)
      echo "Argument not used: $1"
      shift
  esac
done

if $HELP; then
  echo "This script combines LMERT and GNMT. In contrast to lmert_wrapper.sh, GNMT does not "
  echo "run in the background but is restarted as grid array job at each iteration. "
  echo "Use this script for large test sets and lmert_wrapper.sh only for very small test sets."
  echo "Parameters:"
  echo "  -help: Print this help text" 
  echo "  -iter: Number of iterations ($n_iter)" 
  echo "  -num-parts: Number of parallel grid jobs ($num_parts)" 
  echo "  -src: Text file with source sentences ($src)" 
  echo "  -ref: Text file with target sentences ($trg)" 
  echo "  -initial-weights: Initial predictor weights, comma separated" 
  echo "  -lmert-bin: Path to LMERT binary ($lmert_bin)" 
  echo "  -lmert-args: Argument string for LMERT apart from 'lambda'" 
  echo "  -lmert-pipe: Pipe for processing output before passing to evaluation" 
  echo "  -work-dir: Working directory ($work_dir)" 
  echo "  -gnmt-config-file: GNMT config file (passed through to decode.py as --config_file)" 
  exit 0
fi

mkdir -p "$work_dir"

weights="$initial_weights"
set_size=$(cat $ref | wc -l)
decode_script=$(dirname $0)/decode_on_grid_cpu.sh
for i in $(seq $n_iter)
do
  echo "ITERATION $i"
  iter_dir=$work_dir/$i
  mkdir $iter_dir
  echo $weights > $iter_dir/weights.txt
 
  # Create config file
  cp $gnmt_config_file $iter_dir/config.ini
  echo "predictor_weights: $weights" >>  $iter_dir/config.ini
  echo "outputs: fst,nbest" >>  $iter_dir/config.ini
  echo "early_stopping: false" >>  $iter_dir/config.ini

  # Run decoder
  cmd="$decode_script $num_parts $set_size $iter_dir/config.ini $iter_dir"
  echo "DECODE CMD:$cmd"
  eval $cmd

  # Wait
  while [ ! -f $iter_dir/DONE ]
  do
    echo $(date)": Waiting for $iter_dir/DONE..."
    sleep 30
  done

  # Run LMERT
  $(dirname $0)/../compile_veclat_directory.sh $iter_dir/out.fst $iter_dir/out.fst.bin $weights $prev_dir
  prev_dir=$iter_dir/out.fst.bin
  cmd="$lmert_bin --search=random --random_axes --random_directions=28 --direction=axes \
    --cache_lattices --error_function=truebleu --algorithm=lmert \
    --idxlimits=1:$set_size --print_precision=6 --lats=$iter_dir/out.fst.bin/%idx%.fst.gz \
    --lambda=$weights --write_parameters=$iter_dir/weights.out.txt $ref \"$pipe\""
  echo "LMERT CMD: $cmd"
  eval $cmd
  weights=$(cat $iter_dir/weights.out.txt)
done

echo "FINAL WEIGHTS: $weights"
