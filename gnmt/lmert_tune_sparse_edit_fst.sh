#!/bin/bash
# This script implements lmert for tuning parameters of the edit distance transducer based 
# combination scheme

HELP=false
work_dir=./lmert-work
lmert_bin=/home/blue7/aaw35/tools/latmert.v1.8/scripts/latmert
n_iter=2
trg=data/testf.ref.de
nmt_vocab=30003
num_parts=60
while [[ $# -gt 0 ]]; do
  case "$1" in
    "--help")
      shift
      HELP=true;
      ;;
    "--hifst_dir")
      shift;hifst_dir="$1";shift
      ;;
    "--nmt_dir")
      shift;nmt_dir="$1";shift
      ;;
    "--nmt_vocab")
      shift;nmt_vocab="$1";shift
      ;;
    "--num_parts")
      shift;num_parts="$1";shift
      ;;
    "--ref")
      shift;ref="$1";shift
      ;;
    "--lmert_pipe")
      shift;pipe="$1";shift
      ;;
    "--iter")
      shift;n_iter="$1";shift
      ;;
    "--initial_weights")
      shift;initial_weights="$1";shift
      ;;
    "--lmert_bin")
      shift;lmert_bin="$1";shift
      ;;
    "--lmert_args")
      shift;lmert_args="$1";shift
      ;;
    "--work_dir")
      shift;work_dir="$1";shift
      ;;
    *)
      echo "Argument not used: $1"
      shift
  esac
done

if [ -z "$nmt_dir" ]; then
  HELP=true
fi

if [ -z "$hifst_dir" ]; then
  HELP=true
fi

if $HELP; then
  echo "This script tunes the parameters of the edit distance transducer based combination scheme"
  echo "using LMERT."
  echo "Parameters:"
  echo "  --help: Print this help text" 
  echo "  --iter: Number of iterations ($n_iter)" 
  echo "  --hifst_dir: Path to the HiFST lattice directory" 
  echo "  --nmt_dir: Path to the NMT lattice directory" 
  echo "  --nmt_vocab: Size of the NMT vocabulary" 
  echo "  --ref: Text file with target sentences ($trg)" 
  echo "  --num_parts: Number of jobs ($num_parts)" 
  echo "  --initial_weights: Initial predictor weights, comma separated" 
  echo "  --lmert_bin: Path to LMERT binary ($lmert_bin)" 
  echo "  --lmert_args: Argument string for LMERT apart from 'lambda'" 
  echo "  --lmert_pipe: Pipe for processing output before passing to evaluation" 
  echo "  --work_dir: Working directory ($work_dir)" 
  exit 0
fi

mkdir -p "$work_dir"

weights="$initial_weights"
set_size=$(cat $ref | wc -l)

for iter in $(seq $n_iter)
do
  echo "ITERATION $iter"
  mkdir "$work_dir/$iter"

  # Create lattices with current weights
  mkdir -p $work_dir/$iter/log
  echo "bash ../scripts/create_sparse_edit_fst_directory.sh $hifst_dir $nmt_dir $work_dir/$iter/lats \$GRID_ASSIGNED_RANGE $nmt_vocab $weights 2000 3" > $work_dir/$iter/cmd.sh
  rm -r $work_dir/lats
  bash ../scripts/grid/distribute_on_grid.sh $num_parts 1:$set_size $work_dir/$iter/cmd.sh $work_dir/$iter/log
  #qsub -N distribute-on-grid-worker -l mem_free=35G,mem_grab=35G,h_vmem=60G -o $work_dir/$iter/log -e $work_dir/$iter/log -t 1-$num_parts -v total_range=1:$set_size,num_parts=$num_parts,cmd_file=$work_dir/$iter/cmd.sh $(dirname $0)/grid/distribute_on_grid_worker.sh 

  # Wait until finished..
  i=0
  while [ "$i" != "$set_size" ]
  do
    echo $(date)": Waiting ($i/$set_size)..."
    sleep 30
    i=$(ls $work_dir/$iter/lats | wc -l)
  done
  sleep 30

  # Override unks at input with output label, then project to output
  echo "Projection..."
  export TUPLEARC_WEIGHT_VECTOR="$weights"
  ../scripts/apply_to_fst_directory.sh $work_dir/$iter/lats/ $work_dir/$iter/lats.projected "fstprint | awk '{if (\$3 == 999999998) \$3=\$4; print \$0}' | fstcompile --arc_type=tropicalsparsetuple | fstproject | fstrmepsilon | fstdeterminize | fstminimize"
  unset TUPLEARC_WEIGHT_VECTOR

  # Run LMERT
  cmd="$lmert_bin --search=random --random_axes --random_directions=28 --direction=axes \
    --cache_lattices --error_function=truebleu --algorithm=lmert \
    --idxlimits=1:$set_size --print_precision=6 --lats=$work_dir/$iter/lats.projected/%idx%.fst.gz \
    --lambda=$weights --write_parameters=$work_dir/$iter/weights.opt.txt $ref \"$pipe\""
  echo "LMERT command: $cmd"
  eval $cmd
  weights=$(cat $work_dir/$iter/weights.opt.txt)
done
