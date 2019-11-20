#!/usr/bin/env bash

## Introduction:  download and crop s2 images

## note: sometime, has message, Product 68c34c66-6909-4efe-adc7-a56f29e38e83 is not online.
# Triggering retrieval from long term archive.
# solution: wait a few hours, then try again.

#authors: Huang Lingcao
#email:huanglingcao@gmail.com
#add time: 11 November, 2019

# Exit immediately if a command exits with a non-zero status. E: error trace
set -eE -o functrace

co_dir=~/codes/PycharmProjects/ChangeDet_DL

rm need_retry_zip_files.txt || true

#shp=~/Data/Qinghai-Tibet/qtp_thaw_slumps/rts_polygons_s2_2018/qtp_train_polygons_s2_2018_v2.shp
shp=~/Data/Qinghai-Tibet/entire_QTP_images/sentinel-2/autoMapping/QTP_deeplabV3+_3/result_backup/QTP_deeplabV3+_3_exp2_iter30000_prj_post2_chpc_2_latlon.shp

save_dir=../s2_images_autodownload
start_date=2015-01-01
end_date=2019-11-01
could_cover=0.7

${co_dir}/dataTools/download_s2_images.py ${shp} ${save_dir}  -s ${start_date} -e ${end_date} -c ${could_cover}