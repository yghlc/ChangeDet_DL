#!/usr/bin/env bash

# conduct polygon change analysis

#authors: Huang Lingcao
#email:huanglingcao@gmail.com
#add time: 18 February, 2020


# Exit immediately if a command exits with a non-zero status. E: error trace
set -eE -o functrace

cd_code=~/codes/PycharmProjects/ChangeDet_DL

#shp_dir=~/Data/Qinghai-Tibet/beiluhe/thaw_slumps
#shp1=${shp_dir}/train_polygons_for_planet_201707/blh_manu_RTS_utm_201707.shp
#shp2=${shp_dir}/train_polygons_for_planet_201807/blh_manu_RTS_utm_201807.shp
#shp3=${shp_dir}/train_polygons_for_planet_201907/blh_manu_RTS_utm_201907.shp

#shp_dir=~/Data/Qinghai-Tibet/beiluhe/result/result_multi_temporal_changes_17-19July/BLH_change_deeplabV3+_4_exp4_iter30000_2017_2019_tiles
#shp1=${shp_dir}/I0_BLH_change_deeplabV3+_4_exp4_iter30000_post_2017_2019.shp
#shp2=${shp_dir}/I1_BLH_change_deeplabV3+_4_exp4_iter30000_post_2017_2019.shp
#shp3=${shp_dir}/I2_BLH_change_deeplabV3+_4_exp4_iter30000_post_2017_2019.shp


shp_dir=~/Data/Qinghai-Tibet/beiluhe/result/result_multi_temporal_changes_17-19July/BLH_change_deeplabV3+_4_exp3_iter30000_2017_2019_tiles
shp1=${shp_dir}/I0_BLH_change_deeplabV3+_4_exp3_iter30000_post_2017_2019.shp
shp2=${shp_dir}/I1_BLH_change_deeplabV3+_4_exp3_iter30000_post_2017_2019.shp
shp3=${shp_dir}/I2_BLH_change_deeplabV3+_4_exp3_iter30000_post_2017_2019.shp

#-p para_qtp.ini
${cd_code}/thawSlumpChangeDet/polygons_change_analyze.py ${shp1} ${shp2} ${shp3}



