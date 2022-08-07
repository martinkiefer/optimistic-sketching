#!/bin/bash

df="../../Data"
ds="wc98"
for i in {1..40}; do 
    echo "$df - $i"
    ./evaluator 2 $(( 4096*32 )) ${df}/${ds}_keys.bin ${df}/${ds}_values.bin $df/gt/$ds/gt_keys.bin $df/gt/$ds/gt_cnt.bin $df/gt/$ds/gt_sum.bin $df/gt/$ds/gt_min.bin $df/gt/$ds/gt_max.bin >> ./${ds}.csv
done
df="../../Data"
ds="caida"
for i in {1..40}; do 
    echo "$df - $i"
    ./evaluator 2 $(( 4096*32 )) ${df}/${ds}_keys.bin ${df}/${ds}_values.bin $df/gt/$ds/gt_keys.bin $df/gt/$ds/gt_cnt.bin $df/gt/$ds/gt_sum.bin $df/gt/$ds/gt_min.bin $df/gt/$ds/gt_max.bin >> ./${ds}.csv
done
df="../../Data"
ds="nyt"
for i in {1..40}; do 
    echo "$df - $i"
    ./evaluator 2 $(( 4096*32 )) ${df}/${ds}_keys.bin ${df}/${ds}_values.bin $df/gt/$ds/gt_keys.bin $df/gt/$ds/gt_cnt.bin $df/gt/$ds/gt_sum.bin $df/gt/$ds/gt_min.bin $df/gt/$ds/gt_max.bin >> ./${ds}.csv
done
