#!/usr/bin/env bash

# plot the Beiluhe study area at Tibetan Plateau, and sub-images of the gushan thaw slumps from 2017 to 2019

#authors: Huang Lingcao
#email:huanglingcao@gmail.com
#add time: 14 August, 2020

# Exit immediately if a command exits with a non-zero status. E: error trace
set -eE -o functrace

img_dir=~/Data/Qinghai-Tibet/beiluhe/beiluhe_planet/beiluhe_basin

img2017=${img_dir}/201707/20170719_3B_AnalyticMS_SR_mosaic_8bit_rgb_sharpen_new_warp.tif
img2018=${img_dir}/201807/20180725_3B_AnalyticMS_SR_mosaic_8bit_rgb_sharpen_new_warp.tif
img2019=${img_dir}/201907/20190730_3B_AnalyticMS_SR_mosaic_8bit_rgb_sharpen_new_warp.tif

qtp_outline=~/Data/Qinghai-Tibet/Qinghai-Tibet_Plateau_shp/Qinghai-Tibet_Plateau_outline2.shp
beiluhe_shp=~/Data/Qinghai-Tibet/beiluhe/beiluhe_reiver_basin_extent/beiluhe_reiver_basin_extent.shp

# get sub image using gdal_translate  (UTM projection, meters)
xmin=491830
xmax=492165
ymin=3856104
ymax=3856396

function reproject_crop_img(){
    in=$1
    out=$2
    # crop
    gdal_translate  -projwin ${xmin} ${ymax} ${xmax} ${ymin} $in tmp.tif
    # reproject to latlon
    gdalwarp -t_srs EPSG:4326  -overwrite  tmp.tif $out
    rm tmp.tif
}

#reproject_crop_img $img2017 2017.tif
#reproject_crop_img $img2018 2018.tif
#reproject_crop_img $img2019 2019.tif

#width=$(expr ${xmax} - ${xmin})
width=5c  # 5 cm
echo ${width}

qtp=qtp_outline.gmt
beiluhe=beiluhe.gmt
#ogr2ogr -f "GMT"  ${qtp} ${qtp_outline}
#ogr2ogr -f "GMT"  ${beiluhe} ${beiluhe_shp}

# get proj4 for projection
qtp_prj=$(gdalsrsinfo -o proj4 ran.shp "/Users/huanglingcao/Dropbox/Research/09 thermokarst and permafrost mapping/permafrost maps (gis files)/perma_maps_TP/ran/ran.shp")

#echo ${qtp_prj}
#gmt info ${qtp} -C

## plot study area
#gmt begin beilue_study_area tif
#
#    gmt basemap -J"+proj=aea +lat_1=27.5 +lat_2=37.5 +lat_0=0 +lon_0=90 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"/14c \
#    -R75/104/26/40 -B5
#    # plot polygon, fill with lightgray (-G)
#    gmt psxy ${qtp} -Glightgray
#    # plot beiluhe, -W pen attributes (width, color, style)
#    gmt psxy ${beiluhe} -W1p,red,solid
#
#    # (x, y[, font, angle, justify], text
#    # font is a font specification with format [size,][font,][color] where size is text size in points,
#    # font is the font to use, and color sets the font color.
#    echo 92,33, Tibetan Plateau  | gmt text -F+f22p,Helvetica-Bold,black
#
#    echo 95.2,34.9, Beiluhe  | gmt text -F+f10p,Helvetica-Bold,black
#
#gmt end show


## plot an image
gmt begin img_2017_rts_latlon tif

    region=$(gmt grdinfo 2017.tif -Ir)  # get region, return -R/xmin/xmax/ymin/ymax
    gmt grdimage 2017.tif -JU46N/14c

    # FORMAT_GEO_MAP, F: floating point, G: suffix (E, N,W)  # interval: 3 second, .xxxx for four digits
    # add frame and axes
    gmt basemap  -BNElb --FORMAT_GEO_MAP=.xxxxF  -Bx5s -By3s # -B+D"ddd:xxx"  #-BWSne -B5mg5m -B5g5+u"@:8:000m@::"
    # add scale bar
    gmt basemap -Ln0.75/0.1+c35N+w100e+u+f ${region} --FONT_ANNOT_PRIMARY=15p,Helvetica,black --MAP_SCALE_HEIGHT=10p
    # add directional rose
    gmt basemap -Tdn0.9/0.85+w1.5c+lW,E,S,N  --FONT_TITLE=10p,Helvetica,black

gmt end show




## -V Select verbose mode, d for debug
#gmt begin study_area_img_2017_to_2019 tif
#    # multiple plot # 1 row by 3 col,
#    # -M margin
#    # -F size
#    # -R${xmin}/${xmax}/${ymin}/${ymax}
#    # -A autolable
#    gmt subplot begin 2x2 -M0.2c -Fs${width},${width},${width}/?,?,? -JX${width}  -A\(1\) -B -R${xmin}/${xmax}/${ymin}/${ymax} \
#    --FONT_TAG=10p,red
#
#        gmt grdimage 2017.tif -c
#        # add scale bar for on the fist subplot
#        gmt basemap -Ln0.8/0.12+w100+lm --FONT_ANNOT_PRIMARY=10p,Helvetica,red --MAP_SCALE_HEIGHT=5p --MAP_TICK_PEN_PRIMARY=2p,red -c[0,0]
#
#        gmt grdimage 2018.tif -c
#        gmt grdimage 2019.tif -c
#
#    gmt subplot end
#
#gmt end show

#rm 2017.tif 2018.tif 2019.tif


