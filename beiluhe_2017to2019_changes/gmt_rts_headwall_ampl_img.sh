#!/usr/bin/env bash

# plot sub images to show headwall more clear

#authors: Huang Lingcao
#email:huanglingcao@gmail.com
#add time: 13 August, 2020

img_dir=~/Data/Qinghai-Tibet/beiluhe/beiluhe_planet/beiluhe_basin

img2017=${img_dir}/201707/20170719_3B_AnalyticMS_SR_mosaic_8bit_rgb_sharpen_new_warp.tif
img2018=${img_dir}/201807/20180725_3B_AnalyticMS_SR_mosaic_8bit_rgb_sharpen_new_warp.tif
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

crop_img $img2017 2017.tif
crop_img $img2018 2018.tif
crop_img $img2019 2019.tif

#width=$(expr ${xmax} - ${xmin})
width=5c  # 5 cm
echo ${width}

# plot the image one by one
function gmt_one_img(){

    in=$1
#    out=$2
    base=$(basename $1)

    gmt begin test_gridimage png
        # basemap, set x-y projection
        # set extent
        # set frame and axes, SWne -Bpl
#        gmt basemap -JX${width}  \
#        -R${xmin}/${xmax}/${ymin}/${ymax} \
#        -LjBL+w100+lm   # -Bg #+tHello # /5c  # +c-48+w100k+f+o0.5

        # draw the image directly
        gmt grdimage $in

        # add a scale bar: center at (0.5, 0.2), normalized (0-1) bounding box coordinates  (n0.8/0.1)
        #  Cartesian projections: Origin +c is not required, +f is not allowed, and no units should be specified in +w
        # length 100 m (+w100)
        # unit is m (+m)
        # plot vertically (+v)
        # set font size --FONT_LABEL=20p
        # FONT_ANNOT_PRIMARY, set font (size, font type, color)
        gmt basemap -Ln0.8/0.1+w100+lm --FONT_ANNOT_PRIMARY=15p,Helvetica,red --MAP_SCALE_HEIGHT=10p --MAP_TICK_PEN_PRIMARY=2p,red

    gmt end show

}
#gmt_one_img 2017.tif

# -V Select verbose mode, d for debug
gmt begin img_2017_to_2019 tif -Vd
    # multiple plot # 1 row by 3 col,
    # -M margin
    # -F size
    # -R${xmin}/${xmax}/${ymin}/${ymax}
    # -A autolable
    gmt subplot begin 1x3 -M0.2c -Fs${width},${width},${width}/?,?,? -JX${width}  -A\(1\) -B -R${xmin}/${xmax}/${ymin}/${ymax} \
    --FONT_TAG=10p,red

        gmt grdimage 2017.tif -c
        # add scale bar for on the fist subplot
        gmt basemap -Ln0.8/0.12+w100+lm --FONT_ANNOT_PRIMARY=10p,Helvetica,red --MAP_SCALE_HEIGHT=5p --MAP_TICK_PEN_PRIMARY=2p,red -c[0,0]

        gmt grdimage 2018.tif -c
        gmt grdimage 2019.tif -c

    gmt subplot end

gmt end show

rm 2017.tif 2018.tif 2019.tif


