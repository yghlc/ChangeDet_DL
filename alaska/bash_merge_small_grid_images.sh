#!/bin/bash

## Introduction:  bash merge small grid image to adjacent ones

#authors: Huang Lingcao
#email:huanglingcao@gmail.com
#add time: 30 Jan, 2021

# Exit immediately if a command exits with a non-zero status. E: error trace
set -eE -o functrace

grid_shp=~/Data/Arctic/alaska/northern_alaska_extent/NoAK_LandscapePermafrost_11242014_edit_buff100_small_edit.shp

py=~/codes/PycharmProjects/ChangeDet_DL/dataTools/merge_small_gridimg_to_AdjacentGrid.py

for dd in $(ls -d nor*_???????? ); do

    echo $dd
    ${py} ${dd}  ${grid_shp}

done

