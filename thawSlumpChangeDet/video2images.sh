#!/usr/bin/env bash

#convert video to images

set -euxo pipefail

video_to_images(){
    local file=$1
    filename=$(basename "$file")
    extension="${filename##*.}"
    filename_noext="${filename%.*}"

    rm -r ${filename_noext} || true
    mkdir ${filename_noext}

    # for thawSlumps_Arctic_Banks_Island.mov
    ffmpeg -i ${file} -r 10 ${filename_noext}/${filename_noext}_%4d.png

    # for Beiluhe_Gushan_thawslump.mp4
#    ffmpeg -i ${file} -r 1 ${filename_noext}/${filename_noext}_%4d.png

}


video_to_images thawSlumps_Arctic_Banks_Island.mov

#video_to_images Beiluhe_Gushan_thawslump.mp4


