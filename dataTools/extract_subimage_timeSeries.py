#!/usr/bin/env python
# Filename: extract_subimage_timeSeries 
"""
introduction: extract time series sub-images, input:
(1) time series images, (2) time series shape file contain landform polygons, and
(3) change detection results (optional)

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 07 July, 2020
"""

import sys,os
from optparse import OptionParser

sys.path.insert(0,os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import basic_src.io_function as io_function
import basic_src.basic as basic
import basic_src.RSImageProcess as RSImageProcess

sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/Landuse_DL'))
from sentinelScripts.get_subImages import get_sub_image
from sentinelScripts.get_subImages import get_sub_label
from sentinelScripts.get_subImages import get_projection_proj4
from sentinelScripts.get_subImages import check_projection_rasters
from sentinelScripts.get_subImages import meters_to_degress_onEarth
from sentinelScripts.get_subImages import get_image_tile_bound_boxes

# import thest two to make sure load GEOS dll before using shapely
import shapely
import shapely.geometry

import geopandas as gpd
import rasterio


def main(options, args):

    pass


if __name__ == "__main__":
    usage = "usage: %prog [options] polygons_shp image_1_folder image_2_folder ..."
    parser = OptionParser(usage=usage, version="1.0 2020-7-7")
    parser.description = 'Introduction: get sub Images (time series) from multi-temporal images. ' \
                         'The images and shape file should have the same projection.'
    parser.add_option("-b", "--bufferSize",
                      action="store", dest="bufferSize",type=float,
                      help="buffer size is in the projection, normally, it is based on meters")
    parser.add_option("-e", "--image_ext",
                      action="store", dest="image_ext",default = '*.tif',
                      help="the image pattern of the image file")
    parser.add_option("-o", "--out_dir",
                      action="store", dest="out_dir",
                      help="the folder path for saving output files")
    parser.add_option("-n", "--dstnodata", type=int,
                      action="store", dest="dstnodata",
                      help="the nodata in output images")
    parser.add_option("-r", "--rectangle",
                      action="store_true", dest="rectangle",default=False,
                      help="whether use the rectangular extent of the polygon")


    (options, args) = parser.parse_args()
    if len(sys.argv) < 2 or len(args) < 1:
        parser.print_help()
        sys.exit(2)

    # if options.para_file is None:
    #     basic.outputlogMessage('error, parameter file is required')
    #     sys.exit(2)

    main(options, args)