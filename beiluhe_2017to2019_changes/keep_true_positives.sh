#!/usr/bin/env bash

# only keep the true positives of mapped polygons, i.e., remove polygons with IOU less than or equal to 0.5.

#authors: Huang Lingcao
#email:huanglingcao@gmail.com
#add time: 3 July, 2020

# Exit immediately if a command exits with a non-zero status. E: error trace
set -eE -o functrace

code_dir=~/codes/PycharmProjects/Landuse_DL
# folder contains results
# exp7
res_dir=~/Data/Qinghai-Tibet/beiluhe/result/result_multi_temporal_changes_17-19July/BLH_change_deeplabV3+_4_exp7_iter30000_2017_2019_tiles
testid=BLH_change_deeplabV3+_4_exp7_iter30000
test_name=2017_2019


cd ${res_dir}

## exp7 mapped polygons
num=3
for (( n=0; n<${num}; n++ ));
do
    echo $n
    shp_pre=I${n}_${testid}

    ###### the one without post ######
    # ${shp_pre}_${test_name}.shp
    ###### the one after post-processing ######
    # ${shp_pre}_post_${test_name}.shp

     ###### the one after timeIOU ######
     # ${shp_pre}_post_${test_name}_RmOccur.shp
     # ${shp_pre}_post_${test_name}_RmOccur_RmTimeidx.shp
     # ${shp_pre}_post_${test_name}_rmTimeiou.shp

    # remove IOU equal to 0
    ${code_dir}/resultScript/remove_polygons.py ${shp_pre}_post_${test_name}.shp -o ${shp_pre}_post_${test_name}_TP0.shp \
    -f 'IoU' -t 0.00001  --bsmaller

#    # remove IOU samller than 0.5
#    ${code_dir}/resultScript/remove_polygons.py ${shp_pre}_post_${test_name}.shp -o ${shp_pre}_post_${test_name}_TP.shp \
#    -f 'IoU' -t 0.5  --bsmaller
done



cd -

