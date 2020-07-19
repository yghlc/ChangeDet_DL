#!/usr/bin/env bash

# introduction: create mosaic of planet images for QZroad buffer area
# the images have been convert to RGB, and divided based on cloud cover

# run this one in: ~/Data/Qinghai-Tibet/entire_QTP_images/planet_sr_images/QZroad_rgb_image_2019_Jul_Aug

out_res=3
nodata=0
fin_out=QZroad_rgb_image_2019_Jul_Aug_mosaic_${out_res}.tif

function mosaic_a_folder(){

    dir=$1
    cd ${dir}

    folder_name=$(basename $PWD)

    tifs=$(ls *_rgb_sharpen.tif | grep -v mosaic)
    out=${folder_name}_mosaic_${out_res}.tif
    rm ${out}

    gdal_merge.py -o ${out} -a_nodata ${nodata} -init ${nodata} -ps ${out_res} ${out_res} ${tifs}

    cd -
}

for dir in $(ls -d rgb_cloud*per); do
    mosaic_a_folder $dir
done

# merge the different cloud cover, put the one with less cloud cover in the last, overlay others
tif1=rgb_cloud_1_per/rgb_cloud_1_per_mosaic_${out_res}.tif
tif2=rgb_cloud_1_3_per/rgb_cloud_1_3_per_mosaic_${out_res}.tif
tif3=rgb_cloud_3_10_per/rgb_cloud_3_10_per_mosaic_${out_res}.tif

rm ${fin_out}

gdal_merge.py -o ${fin_out} -n ${nodata} -init ${nodata} -ps ${out_res} ${out_res} \
${tif3} ${tif2} ${tif1}


