#!/usr/bin/env bash

## Introduction:  backup zip files of sentinel-2 images

## maybe we can use rsync, which can check whether the file has change or not.

#authors: Huang Lingcao
#email:huanglingcao@gmail.com
#add time: 22 November, 2019

# Exit immediately if a command exits with a non-zero status. E: error trace
set -eE -o functrace


s2_dir=~/Data/Qinghai-Tibet/entire_QTP_images/sentinel-2/s2_images_autodownload/s2_download
backup_dir=~/hlc_cryostore/Qinghai-Tibet/entire_QTP_images/sentinel-2/s2_images_autodownload/s2_download


function cp_no_exist_file(){
    file_name=$1
    if [ ! -f ${backup_dir}/${file_name} ]; then
        cp -p ${file_name}  ${backup_dir}/.
    fi
}

# copy sentinel-2 zip files
cd ${s2_dir}
for zip in $(ls *.zip); do
    echo $zip
    cp_no_exist_file $zip
done

# copy cloud mask files.
for cloud in $(ls *_cloud.tif); do
    echo $cloud
    cp_no_exist_file $cloud
done




