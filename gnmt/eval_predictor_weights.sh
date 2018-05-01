#!/bin/bash
# This script is indented to be used in combination with
# mert.jar
# Predictor weights are evaluated by sending the
# #!gnmt rest and #!gnmt config predictor_weights directives
# to the GNMT process and passing through the validation set.

if [ $# -ne 6 ]; then
  echo "Usage: ./eval_predictor_weights.sh <gnmt-pid> <gnmt-out-fifo> <src_dev_set> <trgt_dev_set> <template> <weights>"
  echo "  Evaluates predictor weights using a running GNMT instance."
  echo "    <gnmt-pid>: Process ID of the GNMT process (must be in input_method=stdin)"
  echo "    <gnmt-out-fifo>: Named pipe which is connected to GNMT stdout"
  echo "    <src_dev_set>: path to source side of dev set with word ids"
  echo "    <trgt_dev_set>: path to target side of dev set with word ids"
  echo "    <template>: How to format the weights, e.g. %f-%f,%f,%f"
  echo "    <weights>: Predictor weights, :-separated"
  exit 1;
fi

GNMT_PID=$1
GNMT_OUT_FIFO="$2"
DEV_SRC="$3"
DEV_TRGT="$4"
TEMPLATE=$5
WEIGHTS=$6

BLEU_SCRIPT="../scripts/multi-bleu.perl"
FORMATTED_WEIGHTS=$(printf $TEMPLATE $(echo $WEIGHTS | tr ':' ' '))
SKIP_LINES=$(echo "1+"$(cat $GNMT_OUT_FIFO | wc -l) | bc)

echo "SET WEIGHTS TO $FORMATTED_WEIGHTS AND RESET"
echo "!gnmt config predictor_weights $FORMATTED_WEIGHTS" > /proc/$GNMT_PID/fd/0
echo "!gnmt reset" > /proc/$GNMT_PID/fd/0
echo "DECODE DEV SET: cat $DEV_SRC > /proc/$GNMT_PID/fd/0 &"
cat $DEV_SRC > /proc/$GNMT_PID/fd/0 

N_DEV=$(wc -l $DEV_SRC | awk '{print $1}')
N_DECODED=$(tail -n +$SKIP_LINES $GNMT_OUT_FIFO | fgrep 'Decoded: ' | wc -l)
while [ $N_DEV != $(tail -n +$SKIP_LINES $GNMT_OUT_FIFO | fgrep 'Decoded: ' | wc -l) ];
do
  echo "DECODING... $N_DECODED/$N_DEV"
  sleep 2
  N_DECODED=$(tail -n +$SKIP_LINES $GNMT_OUT_FIFO | fgrep 'Decoded: ' | wc -l)
done

bleu_result=$(tail -n +$SKIP_LINES $GNMT_OUT_FIFO | fgrep 'Decoded: ' | cut -d' ' -f2- | $BLEU_SCRIPT $DEV_TRGT | tail -1)
echo "BLEU FOR $FORMATTED_WEIGHTS $bleu_result"

# Use $3 for BLEU, $4 for BLEU-1, $5 for BLEU-2...
echo "-"$(echo $bleu_result | tr ',' ' ' | tr '/' ' ' | awk '{print $3}')

