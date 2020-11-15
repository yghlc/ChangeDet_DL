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
xmin=491770
xmax=492195
ymin=3856074
ymax=3856426

function reproject_crop_img(){
    in=$1
    out=$2
    # crop
    gdal_translate  -projwin ${xmin} ${ymax} ${xmax} ${ymin} $in tmp.tif
    # reproject to latlon
    gdalwarp -t_srs EPSG:4326  -overwrite  tmp.tif $out
    rm tmp.tif
}

qtp=qtp_outline.gmt
beiluhe=beiluhe.gmt

ogr2ogr -f "GMT"  ${qtp} ${qtp_outline}
ogr2ogr -f "GMT"  ${beiluhe} ${beiluhe_shp}

reproject_crop_img $img2017 2017.tif
reproject_crop_img $img2018 2018.tif
reproject_crop_img $img2019 2019.tif
#



#width=$(expr ${xmax} - ${xmin})
width=14c  # 5 cm
echo ${width}


# get proj4 for projection
qtp_prj=$(gdalsrsinfo -o proj4 ran.shp "/Users/huanglingcao/Dropbox/Research/09 thermokarst and permafrost mapping/permafrost maps (gis files)/perma_maps_TP/ran/ran.shp")

echo ${qtp_prj}
#gmt info ${qtp} -C

# plot study area
gmt begin beilue_study_area png

    gmt basemap -J"+proj=aea +lat_1=27.5 +lat_2=37.5 +lat_0=0 +lon_0=90 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"/${width} \
    -R75/104/26/40 -B5 --FONT_ANNOT_PRIMARY=18p,Helvetica,black
    # plot polygon, fill with lightgray (-G)
    gmt psxy ${qtp} -Glightgray
    # plot beiluhe, -W pen attributes (width, color, style)
    gmt psxy ${beiluhe} -W1p,red,solid

    # (x, y[, font, angle, justify], text
    # font is a font specification with format [size,][font,][color] where size is text size in points,
    # font is the font to use, and color sets the font color.
    echo 92,33, Tibetan Plateau  | gmt text -F+f24p,Helvetica-Bold,black

    echo 96.5,34.9, Beiluhe  | gmt text -F+f18p,Helvetica-Bold,black

    # add a label
    echo 78,39, \(a\)  | gmt text -F+f20p,Helvetica,black

gmt end #show

x_interval=7s
y_interval=5s

function plot_one_image(){
    img=$1
    out_name=$2
    frame=$3    # -BNElb
    label=$4
    ## plot an image
    gmt begin img_${out_name}_rts_latlon png

        region=$(gmt grdinfo ${img} -Ir)  # get region, return -R/xmin/xmax/ymin/ymax
        gmt grdimage ${img} -JU46N/${width}

        # FORMAT_GEO_MAP,  G: suffix (E, N,W)  # interval: 3 second, .xxxx for four digits
        # add frame and axes # -BNElb
        # --FORMAT_FLOAT_OUT=%.6g for D
        gmt basemap  ${frame}  --FORMAT_FLOAT_OUT=%.5g --FORMAT_GEO_MAP=D  -Bx5s -By3s --FONT_ANNOT_PRIMARY=18p,Helvetica,black # -B+D"ddd:xxx"  #-BWSne -B5mg5m -B5g5+u"@:8:000m@::"
        # add scale bar
        gmt basemap -Ln0.75/0.1+c35N+w100e+u+f ${region} --FONT_ANNOT_PRIMARY=20p,Helvetica,black --MAP_SCALE_HEIGHT=10p
        # add directional rose
        gmt basemap -Tdn0.9/0.80+w2.5c+lW,E,S,N  --FONT_TITLE=18p,Helvetica,black

        region_draw=-R0/14/0/14
        # add label
        echo 1,10.5, ${label}  | gmt text -JX${width} ${region_draw}  -F+f20p,Helvetica,white

        # image acquired time
        echo 7,10.5, July ${out_name}  | gmt text -JX${width} ${region_draw} -F+f20p,Helvetica-Bold,black

        # upslope angle (vector: start point(x,y), direction (angle), length)
        # W for pen, -Sv for the setting of vector arrow,
        echo 10 8 270 3 |gmt plot -JX${width} ${region_draw}  -W2p,yellow,solid  -Sv0.45c+eA
        echo 11.5 6.5 Upslope |gmt text -F+f18p,Helvetica-Bold,yellow

        # a arrow to indicate headwall of thaw slumps
        if [ ${out_name} == "2017"  ]; then
            echo 6.2 4.3 30 1.5 |gmt plot -JX${width} ${region_draw}  -W2p,white,solid  -Sv0.45c+eA
            echo 4.7 4.1 Headwall |gmt text -F+f18p,Helvetica-Bold,white
        fi
        if [ ${out_name} == "2018"  ]; then
            echo 5.7 2.9 30 1.5 |gmt plot -JX${width} ${region_draw}  -W2p,white,solid  -Sv0.45c+eA
            echo 4.2 2.7 Headwall |gmt text -F+f18p,Helvetica-Bold,white
        fi
        if [ ${out_name} == "2019"  ]; then
            echo 5.7 1.4 30 1.5 |gmt plot -JX${width} ${region_draw}  -W2p,white,solid  -Sv0.45c+eA
            echo 4.2 1.2 Headwall |gmt text -F+f18p,Helvetica-Bold,white
        fi

    gmt end #show

}

plot_one_image 2017.tif 2017 -BNElb \(b\)
plot_one_image 2018.tif 2018 -BWStr \(c\)
plot_one_image 2019.tif 2019 -BEStl \(d\)
#
#
## combine there four images, merge the image, and resize them to 967x721 2 by 2
montage beilue_study_area.png img_2017_rts_latlon.png img_2018_rts_latlon.png img_2019_rts_latlon.png \
-geometry 977x729+2+2 out.jpg

#open out.tif
mv out.jpg ~/codes/Texpad/polygon_based_rts_changeDet/figs/rts_multi_images_study_area_v3.jpg

# clean file
rm *.gmt *.png *.tif



##### subplot is hard to adust, especially when the subimage has different extent and projection
### abandon it, then layout this sub-image in powerpoint or other software
##
# -V Select verbose mode, d for debug
#gmt begin study_area_img_2017_to_2019 tif
#    # multiple plot # 1 row by 3 col,
#    # -M margin
#    # -F size
#    # -R${xmin}/${xmax}/${ymin}/${ymax}
#    # -A autolable
#    # -B -R${xmin}/${xmax}/${ymin}/${ymax}
#    gmt subplot begin 2x2 -M0.1c -Ff13c/12c -A\(a\)  --FONT_TAG=10p,red
#
#        #######################################################
#        ## qtp map
##        gmt basemap -J"+proj=aea +lat_1=27.5 +lat_2=37.5 +lat_0=0 +lon_0=90 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"/${width} \
##        -R75/104/26/40 -B5  -c0,0
##        # plot polygon, fill with lightgray (-G)
#        gmt psxy ${qtp} -J"+proj=aea +lat_1=27.5 +lat_2=37.5 +lat_0=0 +lon_0=90 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"/6c\
#          -Glightgray -R75/104/26/40 -B5 -c0,0
##        # plot beiluhe, -W pen attributes (width, color, style)
#        gmt psxy ${beiluhe} -W1p,red,solid -c0,0
#
#        # (x, y[, font, angle, justify], text
#        # font is a font specification with format [size,][font,][color] where size is text size in points,
#        # font is the font to use, and color sets the font color.
#        echo 92,33, Tibetan Plateau  | gmt text -F+f22p,Helvetica-Bold,black  -c0,0
#        echo 95.2,34.9, Beiluhe  | gmt text -F+f10p,Helvetica-Bold,black -c0,0
#
#
#        #######################################################
#        # 2017 images
#        region=$(gmt grdinfo 2017.tif -Ir)  # get region, return -R/xmin/xmax/ymin/ymax
#        # FORMAT_GEO_MAP, F: floating point, G: suffix (E, N,W)  # interval: 3 second, .xxxx for four digits
#        gmt grdimage 2017.tif -JU46N/${width}  -BNElb --FORMAT_GEO_MAP=.xxxxF  -Bx${x_interval} -By${y_interval} -c0,1
#        # add scale bar
#        gmt basemap -Ln0.75/0.1+c35N+w100e+u+f ${region} --FONT_ANNOT_PRIMARY=15p,Helvetica,black --MAP_SCALE_HEIGHT=10p -c0,1
#        # add directional rose
#        gmt basemap -Tdn0.9/0.85+w1.5c+lW,E,S,N  --FONT_TITLE=10p,Helvetica,black -c0,1
#
#
#        #######################################################
#        # 2018 images
#        region=$(gmt grdinfo 2018.tif -Ir)  # get region, return -R/xmin/xmax/ymin/ymax
#        gmt grdimage 2018.tif -JU46N/${width} -BWStr --FORMAT_GEO_MAP=.xxxxF  -Bx${x_interval} -By${y_interval} -c1,0
#
##        # FORMAT_GEO_MAP, F: floating point, G: suffix (E, N,W)  # interval: 3 second, .xxxx for four digits
##        # add frame and axes
##        gmt basemap  -BNElb --FORMAT_GEO_MAP=.xxxxF  -Bx5s -By3s -c[1,0]  # -B+D"ddd:xxx"  #-BWSne -B5mg5m -B5g5+u"@:8:000m@::"
##        # add scale bar
##        gmt basemap -Ln0.75/0.1+c35N+w100e+u+f ${region} --FONT_ANNOT_PRIMARY=15p,Helvetica,black --MAP_SCALE_HEIGHT=10p -c[1,0]
##        # add directional rose
##        gmt basemap -Tdn0.9/0.85+w1.5c+lW,E,S,N  --FONT_TITLE=10p,Helvetica,black -c[1,0]
#
#
#
#        #######################################################
#        # 2019 images
#        region=$(gmt grdinfo 2019.tif -Ir)  # get region, return -R/xmin/xmax/ymin/ymax
#        gmt grdimage 2019.tif -JU46N/${width}   -BSEtl --FORMAT_GEO_MAP=.xxxxF  -Bx${x_interval} -By${y_interval} -c1,1
#
##        # add scale bar
##        gmt basemap -Ln0.75/0.1+c35N+w100e+u+f ${region} --FONT_ANNOT_PRIMARY=15p,Helvetica,black --MAP_SCALE_HEIGHT=10p -c[1,1]
##        # add directional rose
##        gmt basemap -Tdn0.9/0.85+w1.5c+lW,E,S,N  --FONT_TITLE=10p,Helvetica,black -c[1,1]
#
#
#    gmt subplot end
#
#gmt end show

#rm 2017.tif 2018.tif 2019.tif


