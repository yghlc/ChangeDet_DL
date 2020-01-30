#!/usr/bin/env bash

# conduct change detection based on polygons

#authors: Huang Lingcao
#email:huanglingcao@gmail.com
#add time: 10 January, 2020


# Exit immediately if a command exits with a non-zero status. E: error trace
set -eE -o functrace

cd_code=~/codes/PycharmProjects/ChangeDet_DL

#shp_dir=~/Data/Qinghai-Tibet/beiluhe/thaw_slumps
#old_shp=${shp_dir}/train_polygons_for_planet_201707/blh_manu_RTS_utm_201707_36.shp
#new_shp=${shp_dir}/train_polygons_for_planet_201807/blh_manu_RTS_utm_201807_36.shp


shp_dir=~/Data/Qinghai-Tibet/beiluhe/result/result_multi_temporal_changes_17-19July/BLH_change_deeplabV3+_4_exp2_iter30000_2017_2019_36Poly_tiles
#old_shp=${shp_dir}/I0_BLH_change_deeplabV3+_4_exp2_iter30000_post_2017_2019_36Poly.shp
#new_shp=${shp_dir}/I1_BLH_change_deeplabV3+_4_exp2_iter30000_post_2017_2019_36Poly.shp

old_shp=${shp_dir}/I1_BLH_change_deeplabV3+_4_exp2_iter30000_post_2017_2019_36Poly.shp
new_shp=${shp_dir}/I2_BLH_change_deeplabV3+_4_exp2_iter30000_post_2017_2019_36Poly.shp

${cd_code}/thawSlumpChangeDet/polygons_cd.py ${old_shp} ${new_shp} -p para_qtp.ini



