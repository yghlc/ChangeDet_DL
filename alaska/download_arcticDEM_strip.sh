#!/usr/bin/env bash

## Introduction:  download ArcticDEM for the northern slope of Alaska

## maybe we can use rsync, which can check whether the file has change or not.

#authors: Huang Lingcao
#email:huanglingcao@gmail.com
#add time: 25 December, 2020

# Exit immediately if a command exits with a non-zero status. E: error trace
set -eE -o functrace

#ext_shp=~/Data/Arctic/alaska/northern_alaska_extent/NoAK_LandscapePermafrost_11242014_edit_buff100_small.shp
ext_shp=~/Data/Arctic/alaska/NoAK_LandscapePermafrost_GIS_files/NoAK_LandscapePermafrost_GIS_11242014/NoAK_LandscapePermafrost_11242014shp/NoAK_LandscapePermafrost_11242014_edit.shp

# dem indexes shape file, ArcticDEM strip
dem_shp=~/Data/Arctic/ArcticDEM/BROWSE_SERVER/indexes/ArcticDEM_Strip_Index_Rel7/ArcticDEM_Strip_Index_Rel7.shp

py=~/codes/PycharmProjects/ChangeDet_DL/dataTools/download_arcticDEM.py


${py} ${ext_shp} ${dem_shp}


