#!/bin/bash

## Introduction:  bash convert Planet image from 4-band to 3-band (RGB).

#authors: Huang Lingcao
#email:huanglingcao@gmail.com
#add time: 8 Jan, 2021

# Exit immediately if a command exits with a non-zero status. E: error trace
set -eE -o functrace

dir=northern_alaska_2020_Jul_Aug

odir=${dir}_8bit_rgb
mkdir ${odir}

for dd in $(ls -d ${dir}/nor*_???????? ); do

	echo $dd
	folder=$(basename ${dd})

	save_dir=${odir}/${folder}
	mkdir ${save_dir}

	for tif in $(ls ${dd}/*.tif);do

		echo $tif

		filename=$(basename "$tif")
		extension="${filename##*.}"
		filename_noext="${filename%.*}"

		 # to 8bit
        out8bit=${save_dir}/${filename_noext}_8bit.tif
        gdal_translate -ot Byte -scale 0 2000 1 255 -of VRT ${tif} ${out8bit}
        # get RGB
        outrgb=${save_dir}/${filename_noext}_8bit_rgb.tif
        gdal_translate -b 3 -b 2 -b 1 -of GTiff -a_nodata 0 -co compress=lzw -co tiled=yes -co bigtiff=if_safer \
          ${out8bit} ${outrgb}

        rm ${out8bit}

#        exit
	done

#    exit

done

