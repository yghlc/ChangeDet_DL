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

import sentinelsat

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


def download_s2_time_lapse_images(start_date,end_date):
    pass


def main(options, args):

    polygons_shp = args[0]
    save_folder = args[1]  # folder for saving downloaded images

    # check training polygons
    assert io_function.is_file_exist(polygons_shp)
    os.system('mkdir -p ' + save_folder)

    # item_types = options.item_types.split(',') # ["PSScene4Band"]  # , # PSScene4Band , PSOrthoTile

    start_date = datetime.strptime(options.start_date, '%Y-%m-%d') #datetime(year=2018, month=5, day=20)
    end_date = datetime.strptime(options.end_date, '%Y-%m-%d')  #end_date
    could_cover_thr = options.cloud_cover           # 0.3


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


    # # download images
    # download_planet_images(polygons_json, start_date, end_date, could_cover_thr, item_types, save_folder)



    pass



if __name__ == "__main__":

    usage = "usage: %prog [options] polygon_shp save_dir"
    parser = OptionParser(usage=usage, version="1.0 2019-11-09")
    parser.description = 'Introduction: search and download Sentinel-2 images '
    parser.add_option("-s", "--start_date",default='2016-01-01',
                      action="store", dest="start_date",
                      help="start date for inquiry, with format year-month-day, e.g., 2016-01-01")
    parser.add_option("-e", "--end_date",default='2019-12-31',
                      action="store", dest="end_date",
                      help="the end date for inquiry, with format year-month-day, e.g., 2019-12-31")
    parser.add_option("-c", "--cloud_cover",
                      action="store", dest="cloud_cover", type=float,
                      help="the could cover threshold, only accept images with cloud cover less than the threshold")
    # parser.add_option("-i", "--item_types",
    #                   action="store", dest="item_types",default='PSScene4Band',
    #                   help="the item types, e.g., PSScene4Band,PSOrthoTile")


    (options, args) = parser.parse_args()
    if len(sys.argv) < 2 or len(args) < 1:
        parser.print_help()
        sys.exit(2)

    basic.setlogfile('download_s2_images_%s.log' % str(datetime.date(datetime.now())))

    main(options, args)
