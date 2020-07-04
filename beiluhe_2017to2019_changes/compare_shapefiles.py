#!/usr/bin/env python
# Filename: compare shapefiles
"""
introduction: compare two shapefiles

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 04 July, 2020
"""

import os, sys

cd_dir = os.path.expanduser('~/codes/PycharmProjects/ChangeDet_DL')
sys.path.insert(0, os.path.join(cd_dir,'thawSlumpChangeDet'))

from polygons_cd import polygons_change_detection

cur_dir = os.getcwd()

res_dir=os.path.expanduser('~/Data/Qinghai-Tibet/beiluhe/result/result_multi_temporal_changes_17-19July/BLH_change_deeplabV3+_4_exp7_iter30000_2017_2019_tiles')
testid='BLH_change_deeplabV3+_4_exp7_iter30000'
test_name='2017_2019'

os.chdir(res_dir)

## exp7 mapped polygons
num=3

for n in range(num):
    # echo $n
    shp_pre='_'.join(['I%d'%n,testid])

    ###### the one without post ######
    # ${shp_pre}_${test_name}.shp
    ###### the one after post-processing ######
    # ${shp_pre}_post_${test_name}.shp

    ###### the ones after timeIOU ######
    # ${shp_pre}_post_${test_name}_RmOccur.shp
    # ${shp_pre}_post_${test_name}_RmOccur_RmTimeidx.shp
    # ${shp_pre}_post_${test_name}_rmTimeiou.shp

    ###### the ones only keep the true positives (IOU >= 0.5) ######
    # ${shp_pre}_post_${test_name}_TP.shp

    shp1 = '_'.join([shp_pre,'post',test_name,'TP0']) + '.shp'          # ${shp_pre}_post_${test_name}_TP.shp
    shp2 = '_'.join([shp_pre,'post',test_name,'rmTimeiou' ])  + '.shp'   # ${shp_pre}_post_${test_name}_rmTimeiou.shp

    # get expanding and shrinking parts
    output_path_expand = '_'.join(['expand','I%d'%n,'diff_postTP_and_rmTimeiou']) +'.shp'
    output_path_shrink = '_'.join(['shrink', 'I%d' % n, 'diff_postTP_and_rmTimeiou']) + '.shp'
    polygons_change_detection(shp1, shp2, output_path_expand,output_path_shrink)

    pass


os.chdir(cur_dir)


