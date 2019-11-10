#!/usr/bin/env python
# Filename: download_s2_images 
"""
introduction:

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 09 November, 2019
"""

import sys,os
from optparse import OptionParser
from datetime import datetime

from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt

# path for Landuse_DL
sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/Landuse_DL'))
#  import functions,
# also some global variable: downloaed_scene_geometry and manually_excluded_scenes
from planetScripts.download_planet_img import *

def get_and_set_dhub_key(user_name=None):
    '''
    get and set the data hub account
    :return:
    '''
    keyfile = os.path.expanduser('~/.esa_d_hub_account')
    with open(keyfile) as f_obj:
        lines = f_obj.readlines()
        if user_name is None:
            tmp_str = lines[0].strip()      # # remove '\n'
            user_name, password = tmp_str.split(':')
        else:
            for line in lines:
                if user_name in line:
                    tmp_str = line.strip()
                    user_name, password = tmp_str.split(':')
                    break

        # set user name and password
        os.environ["DHUS_USER"] = user_name
        os.environ["DHUS_PASSWORD"] = password
        return True

def down_load_through_sentinel_hub():
    # it seems that through sentinel hub we can download S2 Level 2A images, but need to pay
    pass

def download_s2_time_lapse_images(start_date,end_date, polygon_json, cloud_cover_thr, buffer_size, save_dir):
    '''
    download all s2 images overlap with
    :param start_date: start date of the time lapse images
    :param end_date: end date  of the time lapse images
    :param polygon_json: a polygon in json format
    :param cloud_cover_thr: cloud cover for inquiring images
    :param buffer_size: buffer area for crop the image
    :param save_dir: save folder
    :return:
    '''

    # connect to sentienl API
    basic.outputlogMessage("connecting to sentinel API...")
    # print(os.environ["DHUS_USER"], os.environ["DHUS_PASSWORD"])
    api = SentinelAPI(os.environ["DHUS_USER"], os.environ["DHUS_PASSWORD"]) # data["login"], data["password"], 'https://scihub.copernicus.eu/dhus'

    # inquiry images
    footprint = geojson_to_wkt(polygon_json)

    products = api.query(footprint,
                         date=(start_date, end_date),  # (start, end), e.g. (“NOW-1DAY”, “NOW”)
                         platformname='Sentinel-2',
                         cloudcoverpercentage=(0, cloud_cover_thr*100)
                         )
    if len(products) < 1:
        basic.outputlogMessage('warning, no results, please increase time span or cloud cover')
        return False

    # print(products)       # test
    [print(products[item]) for item in products]


    # check a scene already exist,

    # crop images


    test = 1


    pass

def download_s2_by_tile():
    # test download
    # For orthorectified products (Level-1C and Level-2A):
    # The granules (also called tiles) consist of 100 km by 100 km squared ortho-images in
    # UTM/WGS84 projection. There is one tile per spectral band.
    # For Level-1B, a granule covers approximately 25 km AC and 23 km AL
    # Tiles are approximately 500 MB in size.
    # Tiles can be fully or partially covered by image data. Partially covered tiles
    # correspond to those at the edge of the swath.

    # All data acquired by the MSI instrument are systematically processed up to Level-1C by the ground segment,
    # specifically the Payload Data Ground Segment (PDGS). Level-2A products are
    # generated on user side through the Sentinel-2 Toolbox.

    #Level-2A products are not systematically generated at the ground segment.
    # Level-2A generation can be performed by the user through the Sentinel-2 Toolbox using
    # as input the associated Level-1C product.

    #Level-0 and Level-1A products are PDGS internal products not made available to users.

    # example from https://sentinelsat.readthedocs.io/en/stable/api.html

    from collections import OrderedDict

    api = SentinelAPI(os.environ["DHUS_USER"], os.environ["DHUS_PASSWORD"])

    tiles = ['33VUC', '33UUB']

    query_kwargs = {
        'platformname': 'Sentinel-2',
        'producttype': 'S2MSI1C',
        'date': ('NOW-14DAYS', 'NOW')}

    products = OrderedDict()
    for tile in tiles:
        kw = query_kwargs.copy()
        kw['tileid'] = tile  # products after 2017-03-31
        pp = api.query(**kw)
        products.update(pp)

    api.download_all(products)

def main(options, args):

    polygons_shp = args[0]
    save_folder = args[1]  # folder for saving downloaded images

    # check training polygons
    assert io_function.is_file_exist(polygons_shp)
    os.system('mkdir -p ' + save_folder)

    # item_types = options.item_types.split(',') # ["PSScene4Band"]  # , # PSScene4Band , PSOrthoTile

    start_date = datetime.strptime(options.start_date, '%Y-%m-%d') #datetime(year=2018, month=5, day=20)
    end_date = datetime.strptime(options.end_date, '%Y-%m-%d')  #end_date
    cloud_cover_thr = options.cloud_cover           # 0.3
    crop_buffer = options.buffer_size


    # set account
    if get_and_set_dhub_key() is not True:
        return False

    # read polygons
    polygons_json = read_polygons_json(polygons_shp)

    # read the excluded_scenes before read download images,
    # save to global variable: manually_excluded_scenes
    read_excluded_scenes(save_folder)

    # #read geometry of images already in "save_folder"
    # save to global variable: downloaed_scene_geometry
    read_down_load_geometry(save_folder)

    # test
    # download_s2_by_tile()

    for idx, geom in enumerate(polygons_json):
        basic.outputlogMessage('downloading and cropping images for %d polygon, total: %d polygons'%(idx+1, len(polygons_json)))
        download_s2_time_lapse_images(start_date, end_date, geom, cloud_cover_thr, crop_buffer, save_folder)

        break

    pass



if __name__ == "__main__":

    usage = "usage: %prog [options] polygon_shp save_dir"
    parser = OptionParser(usage=usage, version="1.0 2019-11-09")
    parser.description = 'Introduction: search and download Sentinel-2 images and crop to polyon extents '
    parser.add_option("-s", "--start_date",default='2016-01-01',
                      action="store", dest="start_date",
                      help="start date for inquiry, with format year-month-day, e.g., 2016-01-01")
    parser.add_option("-e", "--end_date",default='2019-12-31',
                      action="store", dest="end_date",
                      help="the end date for inquiry, with format year-month-day, e.g., 2019-12-31")
    parser.add_option("-c", "--cloud_cover",
                      action="store", dest="cloud_cover", type=float, default = 0.1,
                      help="the could cover threshold, only accept images with cloud cover less than the threshold")
    parser.add_option("-b", "--buffer_size",
                      action="store", dest="buffer_size", type=int, default = 500,
                      help="the buffer size to crop image in meters")
    # parser.add_option("-i", "--item_types",
    #                   action="store", dest="item_types",default='PSScene4Band',
    #                   help="the item types, e.g., PSScene4Band,PSOrthoTile")


    (options, args) = parser.parse_args()
    if len(sys.argv) < 2 or len(args) < 1:
        parser.print_help()
        sys.exit(2)

    basic.setlogfile('download_s2_images_%s.log' % str(datetime.date(datetime.now())))

    main(options, args)
