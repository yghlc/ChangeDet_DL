#!/usr/bin/env python
# Filename: extract_subimage_timeSeries 
"""
introduction: extract time series sub-images, input:
(1) time series images, (2) time series shape file contain landform polygons, and
(3) change detection results (optional)

notes: landform polygons can contain change information.

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 07 July, 2020
"""

import sys,os
from optparse import OptionParser

sys.path.insert(0,os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import basic_src.io_function as io_function
import basic_src.basic as basic
import vector_gpd
import basic_src.map_projection as map_projection

sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/Landuse_DL'))
from sentinelScripts.get_subImages import get_sub_image

from sentinelScripts.get_subImages import get_projection_proj4
from sentinelScripts.get_subImages import check_projection_rasters
from sentinelScripts.get_subImages import meters_to_degress_onEarth
from sentinelScripts.get_subImages import get_image_tile_bound_boxes

# import thest two to make sure load GEOS dll before using shapely
import shapely
import shapely.geometry

import geopandas as gpd
import rasterio

import pandas as pd
import parameters

sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/ChangeDet_DL/thawSlumpChangeDet'))
import polygons_change_analyze

def get_union_polygons_at_the_same_loc(shp_list, out_dir='./', union_save_path = None):
    '''
    get the union of mapped polygon at the same location
    :param shp_list:
    :return:
    '''
    if union_save_path is None:
        union_save_path = 'union_of_%s.shp'%'_'.join([str(item) for item in range(len(shp_list))])
    union_save_path = os.path.join(out_dir, union_save_path)   # put to the same folder of first shapefile
    if os.path.isfile(union_save_path):
        basic.outputlogMessage('%s already exist, skip'%union_save_path)
        return vector_gpd.read_polygons_gpd(union_save_path)

    polygons_list_2d = []
    for idx, shp in enumerate(shp_list):
        basic.outputlogMessage('read polygons from %dth shape file'%idx)
        polygons = vector_gpd.read_polygons_gpd(shp)
        polygons_list_2d.append(polygons)

    # get union of polygons at the same location
    union_polygons, occurrence_list, occur_time_list = polygons_change_analyze.get_polygon_union_occurrence_same_loc(polygons_list_2d)

    # save the polygon changes
    union_id_list = [item+1 for item in range(len(union_polygons))]
    occur_time_str_list = []
    for idx_list in occur_time_list:
        time_str = '_'.join([str(item) for item in idx_list])
        occur_time_str_list.append(time_str)

    union_df = pd.DataFrame({'id': union_id_list,
                            'time_occur': occurrence_list,
                            'time_idx': occur_time_str_list,
                            'UnionPolygon': union_polygons
                            })
    wkt_string = map_projection.get_raster_or_vector_srs_info_wkt(shp_list[0])
    vector_gpd.save_polygons_to_files(union_df, 'UnionPolygon', wkt_string, union_save_path)
    basic.outputlogMessage('Save the union polygons to %s'%union_save_path)

    return union_polygons


def get_image_list_2d(input_image_dir,image_folder_list, pattern_list):
    '''
    get image file path at different time.
    :param image_folder_list:
    :param pattern_list:
    :return:
    '''
    image_list_2d = []  # 2D list, for a specific time, it may have multi images

    if len(image_folder_list) != len(pattern_list):
        raise ValueError('The length of image folder list and pattern list is different')

    for image_folder, pattern in zip(image_folder_list, pattern_list):
        # get image tile list
        # image_tile_list = io_function.get_file_list_by_ext(options.image_ext, image_folder, bsub_folder=False)
        folder_path = os.path.join(input_image_dir,image_folder)
        image_tile_list = io_function.get_file_list_by_pattern(folder_path,pattern)
        if len(image_tile_list) < 1:
            raise IOError('error, failed to get image tiles in folder %s'%folder_path)

        check_projection_rasters(image_tile_list)   # it will raise errors if found problems
        image_list_2d.append(image_tile_list)

    return image_list_2d


def organize_change_info(txt_path):


    pass

def get_time_series_subImage_for_polygons(polygons, time_images_2d, save_dir, bufferSize, pre_name, dstnodata, brectangle=True):
    '''
    extract time series sub-images at different polygon location,
    :param polygons:
    :param time_images_2d:
    :param save_dir:
    :param bufferSize:
    :param pre_name:
    :param dstnodata:
    :param brectangle:
    :return:
    '''

    img_tile_boxes_list = []
    time_count = len(time_images_2d)
    for idx in range(time_count):
        img_tile_boxes = get_image_tile_bound_boxes(time_images_2d[idx])
        img_tile_boxes_list.append(img_tile_boxes)

    for idx, c_polygon in enumerate(polygons):
        # output message
        basic.outputlogMessage('obtaining %dth time series sub-images'%idx)

        # get buffer area
        expansion_polygon = c_polygon.buffer(bufferSize)

        # create a folder
        poly_save_dir = os.path.join(save_dir, pre_name + '_poly_%d_timeSeries'%idx)
        io_function.mkdir(poly_save_dir)

        for time in range(time_count):
            image_tile_list = time_images_2d[time]
            img_tile_boxes = img_tile_boxes_list[time]

            # get one sub-image based on the buffer areas
            subimg_shortName = pre_name+'_poly_%d_t_%d.tif'%(idx,time)
            subimg_saved_path = os.path.join(poly_save_dir, subimg_shortName)
            if get_sub_image(idx,expansion_polygon,image_tile_list,img_tile_boxes, subimg_saved_path, dstnodata, brectangle) is False:
                basic.outputlogMessage('Warning, skip the %dth polygon'%idx)



def main(options, args):

    out_dir = options.out_dir
    if out_dir is None: out_dir = './'

    para_file = options.para_file



    dstnodata = parameters.get_string_parameters(para_file, 'dst_nodata')
    dstnodata = int(dstnodata)
    bufferSize = parameters.get_string_parameters(para_file, 'buffer_size')
    bufferSize = int(bufferSize)

    rectangle_ext = parameters.get_string_parameters(para_file, 'b_use_rectangle')
    if 'rectangle' in 'rectangle_ext':
        b_rectangle = True
    else:
        b_rectangle = False

    input_image_dir = parameters.get_string_parameters(para_file, 'input_image_dir')
    input_image_dir = io_function.get_file_path_new_home_folder(input_image_dir)

    poly_shp_list = []
    image_folder_list = []
    image_pattern_list = []
    txt_input = args[0]
    with open(txt_input,'r') as f_obj:
        lines = [item.strip() for item in f_obj.readlines()]

        for idx in range(len(lines)):
            line = lines[idx]
            folder, pattern, polygon_shp = line.split(':')
            polygon_shp = io_function.get_file_path_new_home_folder(polygon_shp)
            poly_shp_list.append(polygon_shp)
            image_folder_list.append(folder)
            image_pattern_list.append(pattern)

    if len(poly_shp_list) < 1:
        raise IOError('No shape file in the list')

    if len(poly_shp_list) != len(image_folder_list):
        raise ValueError('The number of shape file and time image is different')

    # 2D list, for a specific time, it may have multi images.

    image_list_2d = get_image_list_2d(input_image_dir, image_folder_list, image_pattern_list)

    # need to check: the shape file and raster should have the same projection.
    for polygons_shp, image_tile_list in zip(poly_shp_list, image_list_2d):
        if get_projection_proj4(polygons_shp) != get_projection_proj4(image_tile_list[0]):
            raise ValueError('error, the input raster (e.g., %s) and vector (%s) files don\'t have the same projection' % (image_tile_list[0], polygons_shp))

    # check these are EPSG:4326 projection
    if get_projection_proj4(poly_shp_list[0]).strip() == '+proj=longlat +datum=WGS84 +no_defs':
        bufferSize = meters_to_degress_onEarth(bufferSize)


    # get get union of polygons at the same location
    union_polygons = get_union_polygons_at_the_same_loc(poly_shp_list)

    ###################################################################

    # io_function.mkdir(os.path.join(saved_dir,'subImages'))
    # io_function.mkdir(os.path.join(saved_dir,'subLabels'))

    if 'qtb_sentinel2' in image_list_2d[0][0]:
        # for qtb_sentinel-2 mosaic
        # pre_name = '_'.join(os.path.splitext(os.path.basename(image_tile_list[0]))[0].split('_')[:4])
        pass
    else:
        # pre_name = os.path.splitext(os.path.basename(image_tile_list[0]))[0]
        pass
    pre_name = 'Planet_beiluhe'

    # get_sub_images_and_labels(t_polygons_shp, t_polygons_shp_all, bufferSize, image_tile_list,
    #                           saved_dir, pre_name, dstnodata, brectangle=options.rectangle)

    # extract time-series sub-images
    # get_time_series_subImage_for_polygons(polygons, time_images_2d, save_dir, bufferSize, pre_name, dstnodata,
    #                                       brectangle=True):
    get_time_series_subImage_for_polygons(union_polygons,image_list_2d,out_dir,bufferSize, pre_name, dstnodata, brectangle=b_rectangle)


    pass


if __name__ == "__main__":
    usage = "usage: %prog [options] polygon_image_list.txt "
    parser = OptionParser(usage=usage, version="1.0 2020-7-7")
    parser.description = 'Introduction: get sub Images (time series) from multi-temporal images. polygons_shp may contain change information ' \
                         'The images and shape file should have the same projection.'

    parser.add_option("-e", "--image_ext",
                      action="store", dest="image_ext",default = '*.tif',
                      help="the image pattern of the image file")
    parser.add_option("-o", "--out_dir",
                      action="store", dest="out_dir", default = './',
                      help="the folder path for saving output files")

    parser.add_option("-p", "--para_file",
                      action="store", dest="para_file",
                      help="the parameters file")


    (options, args) = parser.parse_args()
    if len(sys.argv) < 2 or len(args) < 1:
        parser.print_help()
        sys.exit(2)

    if options.para_file is None:
        basic.outputlogMessage('error, parameter file is required')
        sys.exit(2)

    main(options, args)