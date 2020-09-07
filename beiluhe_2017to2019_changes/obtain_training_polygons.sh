#!/usr/bin/env bash

# merge ground truths and negative training polygons in Beiluhe from 2017 to 2019

#authors: Huang Lingcao
#email:huanglingcao@gmail.com
#add time: 1 September, 2020

# Exit immediately if a command exits with a non-zero status. E: error trace
set -eE -o functrace

dir=~/Data/Qinghai-Tibet/beiluhe/thaw_slumps

py=~/codes/PycharmProjects/ChangeDet_DL/dataTools/merge_neg_pos_polygons.py

#gt_201707=${dir}/train_polygons_for_planet_201707/blh_manu_RTS_utm_201707.shp
#gt_201807=${dir}/train_polygons_for_planet_201707/blh_manu_RTS_utm_201807.shp
#gt_201907=${dir}/train_polygons_for_planet_201707/blh_manu_RTS_utm_201907.shp

neg_shp=${dir}/train_polygons_for_planet_201907/blh_train_neg_polygons_201907.shp
version=v5

for year in  2017 2018 2019 ; do
    echo $year
    # ground truth
    gt_shp=${dir}/train_polygons_for_planet_${year}07/blh_manu_RTS_utm_${year}07.shp
    echo $gt_shp
    echo $neg_shp

    save_path=${dir}/train_polygons_for_planet_${year}07/blh_train_polygons_${year}07_${version}.shp
    echo $save_path
    $py $gt_shp  $neg_shp -o $save_path

#    exit

done






