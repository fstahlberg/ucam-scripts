#!/bin/bash

HELP=false
work_dir=./lmert-work
lmert_bin=/home/blue7/aaw35/tools/latmert.v1.8/scripts/latmert
n_iter=5
src=data/dev.ids.en
trg=data/dev.ids.fr
while [[ $# -gt 0 ]]; do
  case "$1" in
    "-help")
      shift
      HELP=true;
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
    "-gnmt-pid")
      shift;gnmt_pid="$1";shift
      ;;
    *)
      echo "Argument not used: $1"
      shift
  esac
done

if $HELP; then
  echo "This script combines LMERT and GNMT. GNMT runs in the background in "
  echo "interactive mode and is operated by this script via the PID. "
  echo "Parameters:"
  echo "  -help: Print this help text" 
  echo "  -iter: Number of iterations ($n_iter)" 
  echo "  -src: Text file with source sentences ($src)" 
  echo "  -ref: Text file with target sentences ($trg)" 
  echo "  -initial-weights: Initial predictor weights, comma separated" 
  echo "  -lmert-bin: Path to LMERT binary ($lmert_bin)" 
  echo "  -lmert-args: Argument string for LMERT apart from 'lambda'" 
  echo "  -lmert-pipe: Pipe for processing output before passing to evaluation" 
  echo "  -work-dir: Working directory ($work_dir)" 
  echo "  -gnmt-pid: Process ID of GNMT process in interactive/stdin mode" 
  exit 0
fi

mkdir -p "$work_dir"

weights="$initial_weights"
set_size=$(cat $ref | wc -l)
for i in $(seq $n_iter)
do
  echo "ITERATION $i"
  mkdir "$work_dir/$i"

  # Run decoder
  echo $weights > $work_dir/$i/weights.txt
  cmd="!gnmt config outputs fst"
  echo "GNMT-CMD:$cmd"
  echo $cmd > /proc/$gnmt_pid/fd/0

  cmd="!gnmt config output_path $work_dir/$i/fst"
  echo "GNMT-CMD:$cmd"
  echo $cmd > /proc/$gnmt_pid/fd/0

  cmd="!gnmt config predictor_weights $weights"
  echo "GNMT-CMD:$cmd"
  echo $cmd > /proc/$gnmt_pid/fd/0

  cmd="!gnmt reset"
  echo "GNMT-CMD:$cmd"
  echo $cmd > /proc/$gnmt_pid/fd/0

  cmd="!gnmt decode $src"
  echo "GNMT-CMD:$cmd"
  echo $cmd > /proc/$gnmt_pid/fd/0

  # Wait until decoding is finished
  while [ ! -d "$work_dir/$i/fst" ];
  do
    sleep 15
    echo $(date)" and still decoding..."
  done
  sleep 50

  # Run lmert
  # Note: lmert treats lattice weights as costs (i.e. minimizes them) as GNMT
  # treats them as scores (i.e. maximizes them). We always take the GNMT perspective
  # but we need to invert the weights before we give them to lmert
  #$(dirname $0)/invert_weights_in_fst_directory.sh $work_dir/$i/fst.bin $work_dir/$i/fst.inv
  $(dirname $0)/compile_veclat_directory.sh $work_dir/$i/fst $work_dir/$i/fst.bin
  cmd="$lmert_bin --search=random --random_axes --random_directions=28 --direction=axes \
    --cache_lattices --error_function=truebleu --algorithm=lmert \
    --idxlimits=1:$set_size --print_precision=6 --lats=$work_dir/$i/fst.bin/%idx%.fst.gz \
    --lambda=$weights --write_parameters=$work_dir/$i/weights.opt.txt $ref \"$pipe\""
  echo "LMERT command: $cmd"
  eval $cmd
  weights=$(cat $work_dir/$i/weights.opt.txt)
done

echo "FINAL WEIGHTS: $weights"
