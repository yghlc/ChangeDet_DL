#!/usr/bin/env python
# Filename: merge_small_gridimg_to_AdjacentGrid 
"""
introduction: merge_small_gridimg_to_AdjacentGrid

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 30 January, 2021
"""

import os,sys
from optparse import OptionParser
sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))

import vector_gpd   # on my mac, this vector_gpd also import shapely, need to import it first, otherwise, Segmentation fault: 11

import raster_io
import basic_src.RSImageProcess as RSImageProcess
import basic_src.io_function as io_function

import re
import numpy as np


def find_neighbour_images(samll_img, grid_img_list, buffer=None):
    neighbours = []
    for img_path in grid_img_list:
        if img_path == samll_img:
            continue
        if raster_io.is_two_image_disjoint(samll_img, img_path, buffer=buffer) is False:
            neighbours.append(img_path)
    return neighbours

def get_common_area_grid_polygon(grid_polygons):

    # get the size of the most grid polygons
    grid_poly_areas = [ item.area for item in grid_polygons ]
    # print(grid_poly_areas)
    grid_median_size = np.median(np.array(grid_poly_areas))
    print('median of grid polygon size: %lf'%grid_median_size)

    # get the majority of the size, but quite slow
    # counts = np.bincount(grid_poly_areas)
    # grid_majority_size = np.argmax(counts)
    # print('majority of grid polygon size: %lf'%grid_majority_size)

    return grid_median_size

def get_file_name_pre_subID_tail(image_path):
    basename = os.path.basename(image_path)
    if 'sub' in basename is False:
        raise ValueError('%s is not a sub-image'%basename)
    id_parts = basename.split('sub')[1]
    # print(id_parts)
    id_parts = id_parts.replace('8bit','')  # remove 8bit
    # print(id_parts)
    # ids =  [item for item in  id_parts.split('_') if item.isdigit()]
    # print(ids)
    out = re.findall(r'\d+', id_parts)
    if len(out) < 1:
        raise ValueError('cannot get subID from %s'%image_path)
    # print(out)
    subIDs = '_'.join(out)
    # print(subIDs)

    subIDs_split = basename.split(subIDs)
    if len(subIDs_split) == 2:
        pre_name, tail = basename.split(subIDs)
    elif len(subIDs_split) > 2:
        tail = subIDs_split[-1]
        pre_name = subIDs.join(subIDs_split[:-1])
    else:
        raise ValueError('failed to split based on subIDs: %s, filename: %s'%(subIDs,basename))

    # e.g., 'northern_alaska_2020_Jul_Aug_mosaic_3.0_20200701_sub_', '17', '_8bit_rgb.tif'
    return pre_name, subIDs, tail
    # return '', '', ''

def merge_small_grid_to_AdjacentGrid(grid_img_dir,grid_common_size):
    '''
    merge small grid images to its adjacent ones.
    :param grid_img_dir:
    :param grid_polygons: the common size of grid polygons
    :return:
    '''

    allowed_size = grid_common_size/4    # greater than 1/4, an image smaller than this, only have maximum three neighbours

    grid_img_list = ['','']
    isolated_small_img = []     # some small image don't have neighbours
    while len(grid_img_list) > 1:
        grid_img_list = io_function.get_file_list_by_ext('.tif', grid_img_dir, bsub_folder=False)
        for item in isolated_small_img:
            grid_img_list.remove(item)
        if len(grid_img_list) < 2:
            break

        # # set a buffer area of 5 meters, making it easier to group connected images
        # # if don't set the buffer (None), only grid images with a shared line (not point) is considered as overlap
        # img_boxes = [ raster_io.get_image_bound_box(img_path, buffer=None) for img_path in grid_img_list ]
        # img_area_list = [raster_io.get_area_image_box(item) for item in grid_img_list]

        # find one small image
        samll_img = None
        for img_path in grid_img_list:
            img_area = raster_io.get_area_image_box(img_path)
            if img_area > allowed_size:
                continue
            else:
                samll_img = img_path
                break
        if samll_img is None:
            break
        # find the neighbours of the small image (if they connected)
        neighbours = find_neighbour_images(samll_img,grid_img_list)
        # if cannot find neighbours, increase the buffer because sometime, there is a small gap
        if len(neighbours) == 0:
            neighbours = find_neighbour_images(samll_img, grid_img_list, buffer=5)

        if len(neighbours) == 0:
            isolated_small_img.append(samll_img)
            continue
        elif len(neighbours) > 2:
            raise ValueError('found more than two neighbours for %s'%samll_img)
        else:
            pass

        # merge the small image to the neighbours (larger one)
        neigh_areas = [ raster_io.get_area_image_box(item) for item in neighbours ]
        max_neighbour = neighbours[ neigh_areas.index(max(neigh_areas)) ]

        pre_name, subID, tail = get_file_name_pre_subID_tail(samll_img)
        _, subid_neig, _ = get_file_name_pre_subID_tail(max_neighbour)

        newID = '_'.join([subID,subid_neig])
        merged_img = os.path.join(grid_img_dir, pre_name + newID + tail)

        RSImageProcess.mosaic_crop_images_gdalwarp([samll_img,max_neighbour],merged_img,
                                                   compress='lzw',tiled='yes',bigtiff='if_safer')

        # remove
        io_function.delete_file_or_dir(samll_img)
        io_function.delete_file_or_dir(max_neighbour)

def main(options, args):

    img_dir = args[0]
    grid_polygon_shp = args[1]

    if os.path.isfile(grid_polygon_shp) is False:
        raise IOError('%s not exist'%grid_polygon_shp)

    grid_polygons = vector_gpd.read_polygons_gpd(grid_polygon_shp)

    # some small grid images (after mosaicking and cropping), need to be merged to the adjacent large one.
    grid_common_size = get_common_area_grid_polygon(grid_polygons)
    merge_small_grid_to_AdjacentGrid(img_dir, grid_common_size)


if __name__ == "__main__":

    usage = "usage: %prog [options] image_dir grid_polygon_shp "
    parser = OptionParser(usage=usage, version="1.0 2021-01-30")
    parser.description = 'Introduction: merge small grid imaegs to its adjacent one '

    (options, args) = parser.parse_args()
    # print(options.to_rgb)
    if len(sys.argv) < 2 or len(args) < 1:
        parser.print_help()
        sys.exit(2)

    main(options, args)