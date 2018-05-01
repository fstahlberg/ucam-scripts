#!/bin/bash

HELP=false
num_parts=20
range=1:100
iter=5
dim=""
work_dir=./mert-work
bleu_cmd='../scripts/eval.sh /dev/stdin data/wmap.testf.de data/testf.de'
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
    "--range")
      shift;range="$1";shift
      ;;
    "--dim")
      shift;dim="$1";shift
      ;;
    "--work_dir")
      shift;work_dir="$1";shift
      ;;
    "--bleu_cmd")
      shift;bleu_cmd="$1";shift
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
  echo "This script tunes the single best hypothesis with BOBYQA or simplex. "
  echo "This might be more accurate than LMERT in case of search errors."
  echo "Parameters:"
  echo "  --help: Print this help text" 
  echo "  --num_parts: Number of parallel grid jobs ($num_parts)" 
  echo "  --range: Range of sentence ids to tune on (e.g. 1:2737)" 
  echo "  --dim: Dimensionality. Default: Number of predictors in config file" 
  echo "  --work_dir: Working directory of this script ($work_dir)" 
  echo "  --bleu_cmd: Passed through to MERT script ($bleu_cmd)" 
  echo "  --config_file: SGNMT config file. Must not include predictor_weights or outputs ($config_file)" 
  exit 0
fi

mkdir -p "$work_dir"

bleu_cmd_enc=$(echo $bleu_cmd | tr ' ' '!')
if [ -z "$dim" ]
then
  dim=$(cat $config_file  | egrep '^ *predictors *:' | cut -d':' -f2- | awk -F',' '{print NF}')
fi

mkdir -p $work_dir

if [ "$num_parts" == "0" ]
then
  echo "Run locally!"
  /home/mifs/fs439/bin/jdk1.8.0_65/bin/java -jar /home/mifs/fs439/bin/mert/mert.jar -minWeight 0.0001 -sumEq1 1 -algorithm bobyqa -dim $dim -outputPrefix $work_dir/mert -evalCommand "$(dirname $0)/mert_single_best_eval_local.sh $config_file $range $work_dir $bleu_cmd_enc"
else
  /home/mifs/fs439/bin/jdk1.8.0_65/bin/java -jar /home/mifs/fs439/bin/mert/mert.jar -minWeight 0.0001 -sumEq1 1 -algorithm bobyqa -dim $dim -outputPrefix $work_dir/mert -evalCommand "$(dirname $0)/mert_single_best_eval.sh $config_file $range $num_parts $work_dir $bleu_cmd_enc"
  #/home/mifs/fs439/bin/jdk1.8.0_65/bin/java -jar /home/mifs/fs439/bin/mert/mert.jar -minWeight 0.0001 -algorithm simplex -dim $dim -outputPrefix $work_dir/mert -evalCommand "$(dirname $0)/mert_single_best_eval.sh $config_file $range $num_parts $work_dir $bleu_cmd_enc"
fi
