#!/bin/bash

export LC_ALL=en_GB.utf8

if [ $# -ne 1 ]; then
  echo "Usage: ./eval_t2t_untok.sh <dir>"
  echo "  Delete all checkpoint files in all subdirectories which are not in t"
  exit 1;
fi


for check_dir in $(find $1 -name 'checkpoint' | xargs dirname)
do
  read -r -p "Please confirm cleaning up $check_dir? [y/N] " response
  case "$response" in
    [yY][eE][sS]|[yY]) 
        keep_checkpoint=$(head -1 $check_dir/checkpoint | cut -d'"' -f2)
        if [ -z "$keep_checkpoint" ]; then
          echo "Could not parse checkpoint file. Skipping $check_dir"
        else
          echo "Keeping checkpoint $keep_checkpoint"
          for del_file in $(ls $check_dir/*.index | fgrep -v $keep_checkpoint)
          do
            del_checkpoint=$(basename $del_file .index)
            echo "Deleting $del_checkpoint"
            rm $check_dir/$del_checkpoint.data*
            rm $check_dir/$del_checkpoint.index
            rm $check_dir/$del_checkpoint.meta
            echo 'model_checkpoint_path: "'$keep_checkpoint'"' > $check_dir/checkpoint
            echo 'all_model_checkpoint_paths: "'$keep_checkpoint'"' >> $check_dir/checkpoint
          done
        fi
        ;;
    *)
        echo "Skipping $check_dir"
        ;;
  esac
done

