#!/usr/bin/env bash

# added attributes to ground truths

#authors: Huang Lingcao
#email:huanglingcao@gmail.com
#add time: 10 January, 2020


# Exit immediately if a command exits with a non-zero status. E: error trace
set -eE -o functrace

code_dir=~/codes/PycharmProjects/Landuse_DL

dem=~/Data/Qinghai-Tibet/beiluhe/DEM/srtm_30/beiluhe_srtm30_utm_basinExt.tif
slope=~/Data/Qinghai-Tibet/beiluhe/DEM/srtm_30/beiluhe_srtm30_utm_basinExt_slope.tif


shp_dir=~/Data/Qinghai-Tibet/beiluhe/thaw_slumps
ground_truth_201707=${shp_dir}/train_polygons_for_planet_201707/blh_manu_RTS_utm_201707.shp
ground_truth_201807=${shp_dir}/train_polygons_for_planet_201807/blh_manu_RTS_utm_201807.shp
ground_truth_201907=${shp_dir}/train_polygons_for_planet_201907/blh_manu_RTS_utm_201907.shp


# get the circularity of polygons, it will also add INarea and INperimeter
${code_dir}/resultScript/add_info2Polygons.py ${ground_truth_201707}  -n "circularity"
# added dem info
${code_dir}/resultScript/add_info2Polygons.py ${ground_truth_201707} -r ${dem} -n "dem"
# add slope infor
${code_dir}/resultScript/add_info2Polygons.py ${ground_truth_201707} -r ${slope} -n "slo"


# get the circularity of polygons, it will also add INarea and INperimeter
${code_dir}/resultScript/add_info2Polygons.py ${ground_truth_201807}  -n "circularity"
# added dem info
${code_dir}/resultScript/add_info2Polygons.py ${ground_truth_201807} -r ${dem} -n "dem"
# add slope infor
${code_dir}/resultScript/add_info2Polygons.py ${ground_truth_201807} -r ${slope} -n "slo"


# get the circularity of polygons, it will also add INarea and INperimeter
${code_dir}/resultScript/add_info2Polygons.py ${ground_truth_201907}  -n "circularity"
# added dem info
${code_dir}/resultScript/add_info2Polygons.py ${ground_truth_201907} -r ${dem} -n "dem"
# add slope infor
${code_dir}/resultScript/add_info2Polygons.py ${ground_truth_201907} -r ${slope} -n "slo"


