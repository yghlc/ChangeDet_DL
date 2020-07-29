#!/usr/bin/env python
# Filename: merge several shape files.
"""
introduction:

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 28 July, 2020
"""

import sys,os

sys.path.insert(0,os.path.expanduser('~/codes/PycharmProjects/ChangeDet_DL/dataTools'))

from merge_shapefiles import merge_shape_files

sys.path.insert(0,os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import vector_gpd

shp_dir = os.path.expanduser('~/Data/Qinghai-Tibet/QZrailroad_buffer_area/thaw_slumps_for_training')

# would add more if there are more manual identification results.
shp1 = os.path.join(shp_dir, 'blh_manu_RTS_utm_201907_08.shp')
shp2 = os.path.join(shp_dir, 'QZ_deeplabV3+_2_exp1_iter30000_QZroad_2019_manu_edit.shp')
shp3 = os.path.join(shp_dir, 'QZ_deeplabV3+_2_exp2_iter30000_QZroad_2019_NEW_polygons_edit.shp')
shp_paths = [shp1, shp2, shp3]


#the version 1 is derived from "blh_manu_RTS_utm_201907_08.shp"
# output = os.path.join(shp_dir, 'qz_manu_RTS_utm_201907_08_v2.shp')

# in qz_manu_RTS_utm_201907_08_v3, there are two polygons are close to another one and intersect with others, not duplicated
# edit it to avoid this issue, and save to qz_manu_RTS_utm_201907_08_v3_edit.shp
output = os.path.join(shp_dir, 'qz_manu_RTS_utm_201907_08_v3.shp')
# output = os.path.join(shp_dir, 'qz_manu_RTS_utm_201907_08_v3_edit.shp')

merge_shape_files(shp_paths, output)

#TODO: check any duplicated polygons
vector_gpd.find_polygon_intersec_polygons(output)







