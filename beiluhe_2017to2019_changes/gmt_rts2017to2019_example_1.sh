#!/usr/bin/env bash

# plot sub images to show a example of RTS image from 2017 to 2019
# showing the one retreating 212 meters from 2018 to 2019

#authors: Huang Lingcao
#email:huanglingcao@gmail.com
#add time: 18 October, 2020

img_dir=~/Data/Qinghai-Tibet/beiluhe/beiluhe_planet/beiluhe_basin
shp_dir=~/Data/Qinghai-Tibet/beiluhe/thaw_slumps

img2017=${img_dir}/201707/20170719_3B_AnalyticMS_SR_mosaic_8bit_rgb_sharpen_new_warp.tif
img2018=${img_dir}/201807/20180725_3B_AnalyticMS_SR_mosaic_8bit_rgb_sharpen_new_warp.tif
img2019=${img_dir}/201907/20190730_3B_AnalyticMS_SR_mosaic_8bit_rgb_sharpen_new_warp.tif

shp2017=${shp_dir}/train_polygons_for_planet_201707/blh_manu_RTS_utm_201707.shp
shp2018=${shp_dir}/train_polygons_for_planet_201807/blh_manu_RTS_utm_201807.shp
shp2019=${shp_dir}/train_polygons_for_planet_201907/blh_manu_RTS_utm_201907.shp

# get sub image using gdal_translate
xmin=461396
xmax=462056
ymin=3869388
ymax=3869948

function reproject_crop_img(){
    in=$1
    out=$2
    # crop
    gdal_translate  -projwin ${xmin} ${ymax} ${xmax} ${ymin} $in tmp.tif
    # reproject to latlon
    gdalwarp -t_srs EPSG:4326  -overwrite  tmp.tif $out
    rm tmp.tif
}

reproject_crop_img $img2017 2017.tif
reproject_crop_img $img2018 2018.tif
reproject_crop_img $img2019 2019.tif

# crop a polygon
function get_polygon(){
    in=$1
    out=$2
    ogr2ogr -spat ${xmin} ${ymin} ${xmax} 3869900 -f GMT -t_srs EPSG:4326 ${out} ${1}
}

get_polygon $shp2017 2017.gmt
get_polygon $shp2018 2018.gmt
get_polygon $shp2019 2019.gmt

#width=$(expr ${xmax} - ${xmin})
width=5c  # 5 cm
echo ${width}

#get extent in latlon
extlatlon=$(gmt grdinfo 2017.tif -Ir)     # output
echo ${extlatlon}

region_draw=-R0/14/0/14

# -V Select verbose mode, d for debug  -Vd
gmt begin img_2017_to_2019_ex1 jpg
    # multiple plot # 1 row by 3 col,
    # -M margin
    # -F size
    # -R${xmin}/${xmax}/${ymin}/${ymax}
    # -A autolable
    #  -A\(a\)
    gmt subplot begin 1x3 -M0.05c -Fs${width},${width},${width}/?,?,? -JU46N/${width}  -B  ${extlatlon} \
    --FONT_TAG=10p,red

        gmt grdimage 2017.tif -c
#        gmt psxy 2017.gmt -W0.5p,black,solid -c0,0
        # add scale bar for on the fist subplot
        gmt basemap -Ln0.15/0.15+c35N+w100e ${extlatlon} --FONT_ANNOT_PRIMARY=10p,Helvetica,black --MAP_SCALE_HEIGHT=5p -c0,0

        echo 11,11, July 2017  | gmt text -JX${width} ${region_draw} -F+f10p,Helvetica,black -c0,0

        # upslope arrow (vector: start point(x,y), direction (angle), lenght)
        # W for pen, -Sv for the setting of vector arrow,
        echo 11.0 4.5 130 1.5 |gmt plot -JX${width} ${region_draw}  -W1p,yellow,solid  -Sv0.45c+eA  -c0,0
        echo 11.6 8 Upslope |gmt text -F+f10p,Helvetica,yellow   -c0,0
#
        gmt grdimage 2018.tif -c0,1
#        gmt psxy 2018.gmt -W0.5p,blue,solid -c0,1
        echo 11,11, July 2018  | gmt text -JX${width} ${region_draw} -F+f10p,Helvetica,black  -c0,1

        gmt grdimage 2019.tif -c0,2
#        gmt psxy 2019.gmt -W0.5p,red,solid -c0,2  # this boundaries is not accurate
        echo 11,11, July 2019  | gmt text -JX${width} ${region_draw} -F+f10p,Helvetica,black -c0,2 # Helvetica-Bold

    gmt subplot end

gmt end show

rm 2017.tif 2018.tif 2019.tif
rm 2017.*
rm *.gmt

