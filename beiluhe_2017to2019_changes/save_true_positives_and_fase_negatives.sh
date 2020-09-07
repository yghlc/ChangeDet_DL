#!/usr/bin/env bash

# only keep the false positives and false negatives of mapped polygons

#authors: Huang Lingcao
#email:huanglingcao@gmail.com
#add time: 3 September, 2020

# Exit immediately if a command exits with a non-zero status. E: error trace
set -eE -o functrace

#code_dir=~/codes/PycharmProjects/Landuse_DL
py=~/codes/PycharmProjects/DeeplabforRS/save_FP_FN_polygons.py
# folder contains results

# exp11

testid=BLH_change_deeplabV3+_4_exp12_iter30000
test_name=2017_2019


dir=~/Data/Qinghai-Tibet/beiluhe/result/result_multi_temporal_changes_17-19July
res_dir=${dir}/${testid}_${test_name}_tiles

para_file=para_qtp.ini

function save_tp_fn(){
    n=$1
    echo $n
    shp_pre=I${n}_${testid}


    ${py} ${shp_pre}_post_${test_name}.shp -p ${para_file}

    # for time_iou version
    ${py} ${shp_pre}_post_${test_name}_rmTimeiou.shp -p ${para_file}

}

cd ${res_dir}

## exp7 mapped polygons
num=3

for (( n=0; n<${num}; n++ ));
do
    save_tp_fn $n
done


cd -

