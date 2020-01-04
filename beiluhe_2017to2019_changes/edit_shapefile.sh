#!/usr/bin/env bash

# edit some shape files for the change detection (polygon-based) of thaw slumps in Beiluhe from 2017 to 2019

#authors: Huang Lingcao
#email:huanglingcao@gmail.com
#add time: 4 January, 2020


# Exit immediately if a command exits with a non-zero status. E: error trace
set -eE -o functrace

code_dir=~/codes/PycharmProjects/Landuse_DL


## get the count of adjacent polygons for blh_manu_RTS_utm_201707.shp
ground_truth_201707=~/Data/Qinghai-Tibet/beiluhe/thaw_slumps/train_polygons_for_planet_201707/blh_manu_RTS_utm_201707.shp
${code_dir}/resultScript/add_info2Pylygons.py ${ground_truth_201707}  -n "adj_count" -b 600
