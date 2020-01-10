#!/usr/bin/env bash

# conduct change detection based on polygons

#authors: Huang Lingcao
#email:huanglingcao@gmail.com
#add time: 10 January, 2020


# Exit immediately if a command exits with a non-zero status. E: error trace
set -eE -o functrace

cd_code=~/codes/PycharmProjects/ChangeDet_DL

old_shp=~/Data/Qinghai-Tibet/beiluhe/thaw_slumps/train_polygons_for_planet_201707/blh_manu_RTS_utm_201707_36.shp
new_shp=~/Data/Qinghai-Tibet/beiluhe/thaw_slumps/train_polygons_for_planet_201807/blh_manu_RTS_utm_201807_36.shp

${cd_code}/thawSlumpChangeDet/polygons_cd.py ${old_shp} ${new_shp} -p para_qtp.ini



