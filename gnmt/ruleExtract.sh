#!/bin/bash 

function usage
{
    echo "usage: ruleExtract.sh

Required environment variables:
  HPCYK               : path to the scripts directory
  HADOOP              : path to hadoop binary
  RULEXTRACTJAR       : rule extraction/retrieval jar file
  CFG_RULE_EXTRACTION : rule extraction config file
  RULE_EXTRACTION_HDFSDIR : HDFS directory for rule extraction
  RULE_EXTRACTION_OUTPUT  : final NFS output file

Optional:
  HADOOP_CLIENT_OPTS
  HADOOP_OPTS
"
    exit 1
}

export HADOOP_CLIENT_OPTS=-Xmx30000m
export HADOOP_HEAPSIZE=30000
export HADOOP_OPTS="-XX:+UseConcMarkSweepGC -verbose:gc -server -Xms30000M"

COMPRESS="-Dmapreduce.map.output.compress=true"

## environment variables
if [ -z "$HPCYK" ]; then echo "HPCYK environment variable is required!"; exit; fi
source $HPCYK/scripts/utils.sh

# redirect log to file, if given:
if [ "$1" != "" ]; then redirectStdoutAndStdErr $1; fi
INFO running on `hostname`

zvarcheck "HADOOP RULEXTRACTJAR(f) CFG_RULE_EXTRACTION(f) RULE_EXTRACTION_HDFSDIR RULE_EXTRACTION_OUTPUT" usage
RULEXTRACT="$HADOOP jar $RULEXTRACTJAR"
HDIR=$RULE_EXTRACTION_HDFSDIR

#CMD="$HADOOP fs -rmr $HDIR"
#echo $CMD; $CMD

INFO loading data into hadoop
CMD="$RULEXTRACT uk.ac.cam.eng.extraction.hadoop.util.ExtractorDataLoader \
     --hdfsout=$HDIR/training_data \
     @$CFG_RULE_EXTRACTION"
#echo $CMD; $CMD
echo $CMD

INFO running rule extraction
CMD="$RULEXTRACT uk.ac.cam.eng.extraction.hadoop.extraction.ExtractorJob $COMPRESS \
     -D mapreduce.map.memory.mb=5500 \
     --input=$HDIR/training_data --output=$HDIR/rules \
     @$CFG_RULE_EXTRACTION"
#echo $CMD; $CMD
echo $CMD

INFO calculating source-to-target probabilities
CMD="$RULEXTRACT uk.ac.cam.eng.extraction.hadoop.features.phrase.Source2TargetJob $COMPRESS \
     -D mapreduce.map.memory.mb=5500 \
     -D mapreduce.map.java.opts=-Xmx5000m \
     -D mapreduce.reduce.child.java.opts=-Xmx41000m \
     -D mapreduce.reduce.memory.mb=45000 \
     --input=$HDIR/rules --output=$HDIR/s2t"
echo $CMD; $CMD
echo $CMD

INFO calculating target-to-source probabilities
CMD="$RULEXTRACT uk.ac.cam.eng.extraction.hadoop.features.phrase.Target2SourceJob $COMPRESS \
     -D mapreduce.map.memory.mb=5500 \
     -D mapreduce.map.java.opts=-Xmx5000m \
     -D mapreduce.reduce.child.java.opts=-Xmx41000m \
     -D mapreduce.reduce.memory.mb=45000 \
     --input=$HDIR/rules --output=$HDIR/t2s"
#echo $CMD; $CMD
echo $CMD

wait

#export HADOOP_CLIENT_OPTS=-Xmx30000m
#export HADOOP_HEAPSIZE=30000
#export HADOOP_OPTS="-XX:+UseConcMarkSweepGC -verbose:gc -server -Xms30000M"

INFO merging features
#CMD="$RULEXTRACT uk.ac.cam.eng.extraction.hadoop.merge.MergeJob -D mapred.reduce.tasks=16 \
CMD="$RULEXTRACT uk.ac.cam.eng.extraction.hadoop.merge.MergeJob -D mapred.reduce.tasks=32 \
     --input_features=$HDIR/s2t,$HDIR/t2s \
     --input_rules=$HDIR/rules --output=$HDIR/merge \
     @$CFG_RULE_EXTRACTION"
#echo $CMD; $CMD
echo $CMD

INFO copying hfile to local directory
mkdir -p $RULE_EXTRACTION_OUTPUT
CMD="$HADOOP fs -copyToLocal $HDIR/merge/*.hfile $RULE_EXTRACTION_OUTPUT"
#echo $CMD; $CMD
echo $CMD

INFO done
