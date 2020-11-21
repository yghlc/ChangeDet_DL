#!/bin/bash

## Introduction:  resample an image to coarser resolution
# it put in ~/bin

#authors: Huang Lingcao
#email:huanglingcao@gmail.com
#add time: 20 November, 2020

# Exit immediately if a command exits with a non-zero status. E: error trace
#set -eE -o functrace

# target resolution
res=$1
# input file
file=$2

#out=$3

    filename=$(basename "$file")
    extension="${filename##*.}"
    filename_noext="${filename%.*}"

out=${filename_noext}_${res}.${extension}

gdalwarp -tr $res $res $file $out
