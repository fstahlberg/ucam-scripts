#!/bin/bash

source /data/mifs_scratch/fs439/exp/gnmt/scripts/import_hifst_environment15.sh

HELP=false
num_parts=20
iter=5
lats_dim=6
lats_dir=lats.6gram.sparse_testf
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
    "--lats_dim")
      shift;lats_dim="$1";shift
      ;;
    "--lats_dir")
      shift;lats_dir="$1";shift
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
  echo "This script runs HiFSTs LMERT to jointly optimize predictor weights and weights in an ngram lat"
  echo "Parameters:"
  echo "  --help: Print this help text" 
  echo "  --num_parts: Number of parallel grid jobs ($num_parts)" 
  echo "  --lats_dim: Dimension of sparse weights of lattices in lats_dir ($lats_dim)" 
  echo "  --lats_dir: Directory with ngram lattices (sparse tuple arcs) ($lats_dir)" 
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
script_dir=$(dirname $(dirname $0))

for i in $(seq $iter)
do
  iter_dir=$work_dir/$i
  mkdir $iter_dir
  echo $weights > $iter_dir/weights.txt
  lats_weights=$(echo $weights | cut -d',' -f1-$lats_dim)
  pred_weights=$(echo $weights | cut -d',' -f$lats_dim- | sed 's/^[^,]*,/1.0,/')
  echo "ITERATION $i (lat weight: $lats_weights pred weight: $pred_weights)"

  # Create decoding lattices
  export PARAMS=$lats_weights
  export TUPLEARC_WEIGHT_VECTOR=$lats_weights
  mkdir -p $iter_dir/decode_lats
  for idx in $(seq $set_size)
  do
     cat $lats_dir/$idx.fst | vecmap.O2.bin --dot > $iter_dir/decode_lats/$idx.fst
  done
 
  # Create config file
  cp $config_file $iter_dir/config.ini
  echo "predictor_weights: $pred_weights" >>  $iter_dir/config.ini
  echo "fst_path: $iter_dir/decode_lats/%d.fst" >>  $iter_dir/config.ini
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

  # Combine decoding lats and sgnmt lats
  export TUPLEARC_WEIGHT_VECTOR=$weights
  export PARAMS=$weights
  mkdir $iter_dir/out.fst.combi
  # TODO: The following loops breaks if more than two predictors are used
  cat $(dirname $0)/lmert_ngram_lats_create_combi_lats.sh | sed "s,\$iter_dir,$iter_dir,g" | sed "s,\$lats_dir,$lats_dir,g" | sed "s,\$lats_dim,$lats_dim,g" > $iter_dir/combi_lats.sh
  $(dirname $0)/distribute_on_grid.sh 50 1:$set_size  $iter_dir/combi_lats.sh $iter_dir/combi_logs

  # Wait
  while [ "$(du -b $iter_dir/out.fst.combi/* | awk 'BEGIN{n=0}{if ($1>0) n = n+1}END{print n}')" != "$set_size" ]
  do
    echo $(date)": Waiting for $iter_dir/out.fst.combi reaching $set_size..."
    sleep 30
  done

  # Combine previous lattices with new lattices
  export TUPLEARC_WEIGHT_VECTOR=$weights
  export PARAMS=$weights
  mkdir $iter_dir/out.fst.all
  if [ ! -z $prev_dir ]
  then
    for idx in $(seq $set_size)
    do
      nstates=$(fstinfo $iter_dir/out.fst.combi/$idx.fst | fgrep '# of states' | awk '{print $4}')
      if [ "$nstates" == "0" ]
      then # If composition is empty (eg. no complete hypo found) copy prev lattice
        echo "$idx is empty"
        cp $prev_dir/$idx.fst $iter_dir/out.fst.all/$idx.fst
      else
        fstunion $prev_dir/$idx.fst $iter_dir/out.fst.combi/$idx.fst | fstrmepsilon | fstdeterminize | fstminimize > $iter_dir/out.fst.all/$idx.fst
      fi
    done
  else
    for idx in $(seq $set_size)
    do
      nstates=$(fstinfo $iter_dir/out.fst.combi/$idx.fst | fgrep '# of states' | awk '{print $4}')
      if [ "$nstates" == "0" ]
      then # If composition is empty (eg. no complete hypo found) insert dummy FST
        echo "$idx is empty"
        cat $iter_dir/out.fst/$idx.fst | vecmap.O2.bin --k=1 --stdarc | fstdeterminize | fstminimize | vecmap.O2.bin --k=$lats_dim --tuplearc | fstarcsort > $iter_dir/out.fst.all/$idx.fst
      else
        fstrmepsilon $iter_dir/out.fst.combi/$idx.fst | fstdeterminize | fstminimize > $iter_dir/out.fst.all/$idx.fst
      fi
    done
  fi

  # Run LMERT
  prev_dir=$iter_dir/out.fst.all
  cmd="lmert.O2.bin --range=$range --input=$iter_dir/out.fst.all/?.fst --initial_params=$weights --int_refs=$int_refs --write_params $iter_dir/weights.opt.txt"
  echo "LMERT CMD: $cmd"
  eval $cmd

  # Delete decoding lattices
  rm -r $iter_dir/decode_lats

  # Shift weights in case of negative lambdas
  #offset=$(cat $iter_dir/weights.opt.txt | tr ',' "\n" | awk 'BEGIN{m=0}{if ($1<m) m=$1}END{print m}')
  offset=0
  weights=$(cat $iter_dir/weights.opt.txt | tr ',' "\n" | awk '{print '$offset'*-1+$1}' | tr "\n" ',' | sed 's/,$//')
done

echo "FINAL WEIGHTS: $weights"
export TUPLEARC_WEIGHT_VECTOR=""
export PARAMS=""
