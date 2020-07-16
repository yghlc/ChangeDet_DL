#!/usr/bin/env python
# Filename: get_planet_image_list 
"""
introduction: get images list of downloaded Planet image in time period and spatial extent

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 16 July, 2020
"""

import sys,os
from optparse import OptionParser

sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import basic_src.io_function as io_function
import basic_src.basic as basic
import vector_gpd

from datetime import datetime
import json
import time

# import thest two to make sure load GEOS dll before using shapely
import shapely
from shapely.geometry import mapping # transform to GeJSON format
from shapely.geometry import shape


def get_Planet_SR_image_list_overlap_a_polygon(polygon,geojson_list, save_list_path=None):
    '''
    get planet surface reference (SR) list overlap a polygon (within or overlap part of the polygon)
    :param polygon: polygon in the shapely format
    :param geojson_list:
    :param save_list_path: save the list to a txt file.
    :return:
    '''

    image_path_list = []
    for geojson_file in geojson_list:
        # print(geojson_file)
        with open(geojson_file) as json_obj:
            geom = json.load(json_obj)
        img_ext = shape(geom)

        inter = polygon.intersection(img_ext)
        if inter.is_empty is False:
            img_dir = os.path.splitext(geojson_file)[0]
            sr_img_paths = io_function.get_file_list_by_pattern(img_dir,'*_SR.tif')
            if len(sr_img_paths) < 1:
                basic.outputlogMessage('warning, no Planet SR image in the %s'%img_dir)
            elif len(sr_img_paths) > 1:
                basic.outputlogMessage('warning, more than one Planet SR image in the %s'%img_dir)
            else:
                image_path_list.append(sr_img_paths[0])

    if save_list_path is not None:
        with open(save_list_path,'w') as f_obj:
            for image_path in image_path_list:
                f_obj.writelines(image_path + '\n')

    return image_path_list

def main(options, args):

    image_dir = args[0]
    shp_path = args[1]

    geojson_list = io_function.get_file_list_by_ext('.geojson',image_dir,bsub_folder=True)
    if len(geojson_list) < 1:
        raise ValueError('There is no geojson files in %s'%image_dir)

    # get files
    extent_polygons = vector_gpd.read_polygons_gpd(shp_path)
    for idx, polygon in enumerate(extent_polygons):
        save_list_txt = 'planet_sr_image_poly_%d.txt'%idx
        get_Planet_SR_image_list_overlap_a_polygon(polygon,geojson_list,save_list_path=save_list_txt)

        pass




    #TODO: filter the image using the acquired time


    pass

if __name__ == "__main__":

    usage = "usage: %prog [options] image_dir polygon_shp "
    parser = OptionParser(usage=usage, version="1.0 2020-07-16")
    parser.description = 'Introduction: get planet image list  '
    # parser.add_option("-s", "--start_date",default='2018-04-30',
    #                   action="store", dest="start_date",
    #                   help="start date for inquiry, with format year-month-day, e.g., 2018-05-23")
    # parser.add_option("-e", "--end_date",default='2018-06-30',
    #                   action="store", dest="end_date",
    #                   help="the end date for inquiry, with format year-month-day, e.g., 2018-05-23")
    # parser.add_option("-c", "--cloud_cover",
    #                   action="store", dest="cloud_cover", type=float,
    #                   help="the could cover threshold, only accept images with cloud cover less than the threshold")
    # parser.add_option("-i", "--item_types",
    #                   action="store", dest="item_types",default='PSScene4Band',
    #                   help="the item types, e.g., PSScene4Band,PSOrthoTile")
    # parser.add_option("-a", "--planet_account",
    #                   action="store", dest="planet_account",default='huanglingcao@link.cuhk.edu.hk',
    #                   help="planet email account, e.g., huanglingcao@link.cuhk.edu.hk")



    (options, args) = parser.parse_args()
    if len(sys.argv) < 2 or len(args) < 1:
        parser.print_help()
        sys.exit(2)

    basic.setlogfile('download_planet_images_%s.log'%str(datetime.date(datetime.now())))

    main(options, args)

