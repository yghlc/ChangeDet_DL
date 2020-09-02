#!/usr/bin/env bash

# plot two sub-figure: (a) RTS boundaries in 2017, 2018, and 2019, (b) the union

# not finish, but modifiy the orignal QGIS version and get the new figure.

#authors: Huang Lingcao
#email:huanglingcao@gmail.com
#add time: 2 September, 2020

img_dir=~/Data/Qinghai-Tibet/beiluhe/beiluhe_planet/beiluhe_basin

#img2017=${img_dir}/201707/20170719_3B_AnalyticMS_SR_mosaic_8bit_rgb_sharpen_new_warp.tif
#img2018=${img_dir}/201807/20180725_3B_AnalyticMS_SR_mosaic_8bit_rgb_sharpen_new_warp.tif
# chose 2019 image as the background
img2019=${img_dir}/201907/20190730_3B_AnalyticMS_SR_mosaic_8bit_rgb_sharpen_new_warp.tif

# get sub image using gdal_translate
xmin=491830
xmax=492165
ymin=3856104
ymax=3856396

function crop_img(){
    in=$1
    out=$2
    gdal_translate  -projwin ${xmin} ${ymax} ${xmax} ${ymin} $in $out
}

#crop_img $img2019 2019.tif

width=6c

# -V Select verbose mode, d for debug
gmt begin img_union_polygon tif
    # multiple plot # 1 row by 3 col,
    # -M margin
    # -F size
    # -R${xmin}/${xmax}/${ymin}/${ymax}
    # -A autolable
    gmt subplot begin 1x2 -M0.05c -Fs${width},${width}/?,? -JX${width}  -A\(a\) -B -R${xmin}/${xmax}/${ymin}/${ymax} \
    --FONT_TAG=10p,red

        # plot background images and scale bar
        gmt grdimage 2019.tif -c
        gmt basemap -Ln0.8/0.10+w60+lm --FONT_ANNOT_PRIMARY=10p,Helvetica,black --MAP_SCALE_HEIGHT=5p --MAP_TICK_PEN_PRIMARY=1p,black -c0,0

        # plot three polygons



        gmt grdimage 2019.tif -c

        # add scale bar for on the fist subplot
#

    gmt subplot end

gmt end show



# clean
#rm 2019.tif


