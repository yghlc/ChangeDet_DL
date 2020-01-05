#!/usr/bin/env bash

# edit some shape files for the change detection (polygon-based) of thaw slumps in Beiluhe from 2017 to 2019

#authors: Huang Lingcao
#email:huanglingcao@gmail.com
#add time: 4 January, 2020


# Exit immediately if a command exits with a non-zero status. E: error trace
set -eE -o functrace

code_dir=~/codes/PycharmProjects/Landuse_DL

ground_truth_201707=~/Data/Qinghai-Tibet/beiluhe/thaw_slumps/train_polygons_for_planet_201707/blh_manu_RTS_utm_201707.shp

ground_truth_201707_36=~/Data/Qinghai-Tibet/beiluhe/thaw_slumps/train_polygons_for_planet_201707/blh_manu_RTS_utm_201707_36.shp
ground_truth_201807_36=~/Data/Qinghai-Tibet/beiluhe/thaw_slumps/train_polygons_for_planet_201807/blh_manu_RTS_utm_201807_36.shp
ground_truth_201907_36=~/Data/Qinghai-Tibet/beiluhe/thaw_slumps/train_polygons_for_planet_201907/blh_manu_RTS_utm_201907_36.shp

## get the count of adjacent polygons for blh_manu_RTS_utm_201707.shp, buffer area = 600 meters
#${code_dir}/resultScript/add_info2Pylygons.py ${ground_truth_201707}  -n "adj_count" -b 600

## get the circularity of polygons, it will also add area and perimeter
#${code_dir}/resultScript/add_info2Pylygons.py ${ground_truth_201707}  -n "circularity"



