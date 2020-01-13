#!/usr/bin/env python
# Filename: points2polygon 
"""
introduction: convert many points to a polygon

for a file in /Users/huanglingcao/Data/Greenland/ablation_zones

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 13 January, 2020
"""

import sys,os
from optparse import OptionParser

sys.path.insert(0,os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import basic_src.io_function as io_function
import basic_src.basic as basic

# import these two to make sure load GEOS dll before using shapely
import shapely
from shapely.geometry import mapping # transform to GeJSON format
import geopandas as gpd
from shapely.geometry import Point
from shapely.geometry import Polygon

import vector_gpd

import pandas as pd
import geopandas as gpd

def main(options, args):
    points_path = args[0]
    output = args[1]

    proj = options.projection
    crs = {'init': proj}

    with open(points_path) as f_obj:
        lines = f_obj.readlines()

        lon_lat_list = [line.split() for line in lines]

        point_list = [ (float(lon_lat[0]), float(lon_lat[1])) for lon_lat in lon_lat_list]

        # to a polygon
        a_polygon = Polygon(point_list)
        data_frame = pd.DataFrame({'Polygons': [a_polygon]})
        poly_df = gpd.GeoDataFrame(data_frame, crs=crs, geometry='Polygons')
        poly_df.to_file(output, driver='ESRI Shapefile')

        # to points
        # point_list = [ Point(point) for point in point_list ]
        # data_frame = pd.DataFrame({'Points': point_list})
        # poly_df = gpd.GeoDataFrame(data_frame, crs=crs, geometry='Points')
        # poly_df.to_file(output, driver='ESRI Shapefile')


    pass


if __name__ == "__main__":
    usage = "usage: %prog [options] point_file output"
    parser = OptionParser(usage=usage, version="1.0 2020-1-13")
    parser.description = 'Introduction: convert points to a polygons. '
    parser.add_option("-p", "--projection",
                      action="store", dest="projection", default='EPSG:4326',
                      help="the projection of the projection ")

    (options, args) = parser.parse_args()
    if len(sys.argv) < 2 or len(args) < 1:
        parser.print_help()
        sys.exit(2)

    # if options.para_file is None:
    #     basic.outputlogMessage('error, parameter file is required')
    #     sys.exit(2)

    main(options, args)


