#!/usr/bin/env python
# Filename: merge_small_gridimg_to_AdjacentGrid_test.py
"""
introduction: "pytest merge_small_gridimg_to_AdjacentGrid_test.py " or "pytest " for test, add " -s for allowing print out"

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 30 January, 2021
"""
import os,sys

sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import vector_gpd

code_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,code_dir)


import merge_small_gridimg_to_AdjacentGrid

def test_merge_small_grid_to_AdjacentGrid():


    img_dir = '~/Data/Arctic/alaska/northern_alaska_2020_Jul_Aug_8bit_rgb/northern_alaska_2020_Jul_Aug_mosaic_3.0_20200701'
    img_dir = os.path.expanduser(img_dir)

    # merge_small_gridimg_to_AdjacentGrid.merge_small_grid_to_AdjacentGrid(img_dir, 2500000000)

def test_get_common_area_grid_polygon():
    grid_polygon_shp = '~/Data/Arctic/alaska/northern_alaska_extent/NoAK_LandscapePermafrost_11242014_edit_buff100_small_edit.shp'
    grid_polygon_shp = os.path.expanduser(grid_polygon_shp)

    grid_polygons = vector_gpd.read_polygons_gpd(grid_polygon_shp)
    # merge_small_gridimg_to_AdjacentGrid.get_common_area_grid_polygon(grid_polygons)

def test_get_file_name_pre_subID_tail():
    # test1 = 'northern_alaska_2020_Jul_Aug_mosaic_3.0_20200701_sub_161_8bit_rgb.tif'
    # pre, subids, tail = merge_small_gridimg_to_AdjacentGrid.get_file_name_pre_subID_tail(test1)
    # print()
    # print(pre, subids, tail)
    # image_path = 'northern_alaska_2020_Jul_Aug_mosaic_3.0_20200701_sub_24_23.tif'
    # pre, subids, tail = merge_small_gridimg_to_AdjacentGrid.get_file_name_pre_subID_tail(image_path)
    # print(pre, subids, tail)
    # image_2 = 'northern_alaska_2020_Jul_Aug_mosaic_3.0_20200701_sub_16_24_23_17_8bit_rgb.tif'
    # pre, subids, tail = merge_small_gridimg_to_AdjacentGrid.get_file_name_pre_subID_tail(image_2)
    # print(pre, subids, tail)

    test3 = 'northern_alaska_2020_Jul_Aug_mosaic_3.0_20200704_sub_20_8bit_rgb.tif'
    pre, subids, tail = merge_small_gridimg_to_AdjacentGrid.get_file_name_pre_subID_tail(test3)
    print(pre, subids, tail)


if __name__ == '__main__':

    pass