#!/usr/bin/env python
# Filename: cal_relative_dem 
"""
introduction: to calculate the relative elevation for change polygons.
# the elevation of change polygons, comparing with the elevation of old thaw slumps,
# a higher elevation indicates at a upslope location.

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 02 February, 2020
"""

import sys,os
from optparse import OptionParser

sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import basic_src.basic as basic
from vector_features import shape_opeation

# import thest two to make sure load GEOS dll before using shapely
import shapely
import shapely.geometry
import rasterio
from rasterio.mask import mask
from shapely.geometry import mapping # transform to GeJSON format

import geopandas as gpd
import numpy as np

def get_mean_elevation_of_polygons(shp_path, dem_path, nodata):
    '''
    get the dem mean value inside polygons,
    :param shp_path:
    :param dem_path:
    :param nodata:
    :return:  a list of dem mean value
    '''

    # another version of getting mean values from raster inside a polygon can be found in  vector_features.py

    # read polygons
    gpd_shapefile = gpd.read_file(shp_path)
    # class_labels = gpd_shapefile['class_int'].tolist()
    polygons = gpd_shapefile.geometry.values

    dem_mean_list = []

    # read raster
    with rasterio.open(dem_path) as src:

        for polygon in polygons:

            polygon_json = mapping(polygon)
            out_image, out_transform = mask(src, [polygon_json], nodata=nodata, all_touched=True, crop=True)

            # calculate mean value
            dem_values = out_image.flatten()        # to 1D
            # remove nodata element
            dem_values = dem_values[dem_values != nodata]

            dem_mean_list.append(np.mean(dem_values))

    return dem_mean_list

def cal_relative_dem(expand_shp, old_shp, dem_path, nodata = 0):
    '''
    calculate the relative elevation for change polygons, a higher elevation indicates at upslope location.
    the value will be saved in expand_shp, backup this file if necessary

    :param expand_shp: shape file of changes polygons (expanding areas)
    :param old_shp: shape file of old polygons for change detection
    :param dem_path: raster dem files
    :param nodata:
    :return: True if successful
    '''


    # calculate mean elevation of polygons in expand_shp, also find the polygon index (start from 0) old_shp
    expand_polygons_dem = get_mean_elevation_of_polygons(expand_shp, dem_path, nodata)

    # the polygon index in old_shp for polygon-based change detection
    gpd_shapefile = gpd.read_file(expand_shp)
    old_index_list = gpd_shapefile['old_index'].tolist()

    # calculate mean elevation of in old shp
    old_polygon_dem = get_mean_elevation_of_polygons(old_shp, dem_path, nodata)

    relative_dem_list = []
    for idx, (dem_value, old_poly_idx) in enumerate(zip(expand_polygons_dem, old_index_list)):
        if old_poly_idx < 0:
            dem_diff = 0
            basic.outputlogMessage('Warning, no corresponding old polygon for %dth (0 index) record '%idx)
        else:
            dem_diff =  dem_value - old_polygon_dem[old_poly_idx]
        relative_dem_list.append(dem_diff)

    ## save the distance to shapefile
    shp_obj = shape_opeation()
    shp_obj.add_one_field_records_to_shapefile(expand_shp, relative_dem_list, 'diff_dem')

    basic.outputlogMessage('Save DEM difference (diff_dem, a positive indicate upslope) to %s'%expand_shp)

    return True


def main(options, args):

    change_polygon_shp = args[0]
    old_polygon_shp = args[1]
    dem_file = args[2]
    cal_relative_dem(change_polygon_shp, old_polygon_shp, dem_file, nodata = 0)





if __name__ == "__main__":
    usage = "usage: %prog [options] change_polygon.shp old_polygons.shp dem.tif"
    parser = OptionParser(usage=usage, version="1.0 2020-01-31")
    parser.description = 'Introduction: calculate the relative elevation for change polygons '

    parser.add_option("-p", "--para",
                      action="store", dest="para_file",
                      help="the parameters file")

    parser.add_option('-o', '--output',
                      action="store", dest = 'output',
                      help='the path to save the change detection results')

    (options, args) = parser.parse_args()
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(2)

    # # set parameters files
    # if options.para_file is None:
    #     print('error, no parameters file')
    #     parser.print_help()
    #     sys.exit(2)
    # else:
    #     parameters.set_saved_parafile_path(options.para_file)

    basic.setlogfile('polygons_changeDetection.log')

    main(options, args)