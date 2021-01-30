#!/usr/bin/env python
# Filename: mosaic_images_crop_grid_test.py 
"""
introduction: "pytest mosaic_images_crop_grid_test.py " or "pytest " for test, add " -s for allowing print out"

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 30 January, 2021
"""
import os,sys

sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import vector_gpd

code_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,code_dir)


import mosaic_images_crop_grid

def test_merge_small_grid_to_AdjacentGrid():


    img_dir = '~/Data/Arctic/alaska/northern_alaska_2020_Jul_Aug_8bit_rgb/northern_alaska_2020_Jul_Aug_mosaic_3.0_20200701'
    img_dir = os.path.expanduser(img_dir)

    mosaic_images_crop_grid.merge_small_grid_to_AdjacentGrid(img_dir, 2500000000)

def test_get_common_area_grid_polygon():
    grid_polygon_shp = '~/Data/Arctic/alaska/northern_alaska_extent/NoAK_LandscapePermafrost_11242014_edit_buff100_small_edit.shp'
    grid_polygon_shp = os.path.expanduser(grid_polygon_shp)

    # grid_polygons = vector_gpd.read_polygons_gpd(grid_polygon_shp)
    # mosaic_images_crop_grid.get_common_area_grid_polygon(grid_polygons)


if __name__ == '__main__':

    pass