

source /data/mifs_scratch/fs439/exp/gnmt/scripts/import_hifst_environment15.sh

for idx in $(seq $(echo $GRID_ASSIGNED_RANGE | cut -d':' -f1) $(echo $GRID_ASSIGNED_RANGE | cut -d':' -f2))
do
  if [ "$(du -b $lats_dir/$idx.fst | cut -f1)" -gt "100000000" ]
  then
    echo "$lats_dir/$idx.fst is too large"
    echo '' | fstcompile --arc_type=tropicalsparsetuple > $iter_dir/out.fst.combi/$idx.fst
  else
    cat $iter_dir/out.fst/$idx.fst |  fstprint | sed 's/\s0,1,[^,]\+,/\t0,/' | awk -F',' 'BEGIN { OFS=",";}{for (i=2;i<NF;i++) {$i = $i+'$lats_dim'-1} print $0}' | fstcompile --arc_type=tropicalsparsetuple | fstdeterminize | fstminimize | fstarcsort | fstcompose - $lats_dir/$idx.fst | fstmap --map_type=arc_sum | fstdeterminize | fstminimize | fstrmepsilon | fstdeterminize | fstminimize > $iter_dir/out.fst.combi/$idx.fst
    #cat $iter_dir/out.fst/$idx.fst | vecmap.O2.bin --k=1 --stdarc | fstdeterminize | fstminimize | vecmap.O2.bin --k=$lats_dim --tuplearc | fstarcsort | fstcompose - $lats_dir/$idx.fst | fstmap --map_type=arc_sum | fstdeterminize | fstminimize | fstrmepsilon | fstdeterminize | fstminimize > $iter_dir/out.fst.combi/$idx.fst
  fi
done

