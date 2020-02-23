#!/usr/bin/env python
# Filename: remove_nonActive_thawSlumps 
"""
introduction:

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 22 February, 2020
"""
import sys,os
from optparse import OptionParser

# added path of DeeplabforRS
sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import basic_src.basic as basic
import basic_src.map_projection as map_projection
import basic_src.io_function as io_function

import parameters
import geopandas as gpd
import vector_gpd
import numpy as np


def get_polygon_idx_and_time_iou(ref_polygon, shapefile_gpd):
    for idx, row in shapefile_gpd.iterrows():
        polygon = row['geometry']
        intersection = ref_polygon.intersection(polygon)
        if intersection.is_empty:
            continue
        return idx, row['time_iou']

def remove_non_active_thaw_slumps(shp_list,para_file):
    '''
    remove polygons based on information from multi-temporal polygons
    :param shp_list: a list of shapefile, from oldest to newest
    :param para_file: para file list
    :return:
    '''

    new_shp_list = []
    # remove polygons based on time occurrence ('time_occur')
    normal_occurrence = len(shp_list)       # the expected count
    for idx, shp_file in enumerate(shp_list):
        # remove occurance
        save_shp = io_function.get_name_by_adding_tail(shp_file, 'RmOccur')
        vector_gpd.remove_polygon_equal(shp_file,'time_occur',normal_occurrence, True,save_shp)
        new_shp_list.append(save_shp)

    ### remove polygons based on time iou ('time_iou'), as a thaw slump develop, the time_iou should be increase
    # ready time_iou to 2D list
    shapefile_list = []
    for idx, shp in enumerate(new_shp_list):
        shapefile = gpd.read_file(shp)

        if 'time_iou' not in shapefile.keys():
            raise ValueError('error, %s do not have time_iou, please conduct polygon_change_analyze first'%shp)
        shapefile_list.append(shapefile)
        # print(shapefile.keys())
        # print(shapefile['time_iou'])
        # print(len(shapefile.geometry.values))

    # remove polygons the time_iou are not monotonically increasing
    # after remove based on time occurrence, the polygon number in all shape file should be the same
    time_iou_1st = shapefile_list[0]['time_iou']
    rm_polygon_idx_2d = []
    for idx, time_iou_value in enumerate(time_iou_1st): # shapefile_list[0].geometry.values
        # read time iou
        time_iou_values = [time_iou_value]
        idx_list = [idx]
        polygon = shapefile_list[0].geometry.values[idx]
        # read other polygon and time_iou in other shape file
        for time in range(1, normal_occurrence):
            t_idx, t_iou = get_polygon_idx_and_time_iou(polygon,shapefile_list[time])
            time_iou_values.append(t_iou)
            idx_list.append(t_idx)

        # check if time iou is monotonically increasing
        if np.all(np.diff(time_iou_values) >= 0) is False:
            basic.outputlogMessage('The areas of Polygons %s in temporal shapefile is not monotonically increasing, remove them'%(str(idx_list)))
            rm_polygon_idx_2d.append(idx_list)

    remove_count = len(rm_polygon_idx_2d)
    for rm_idx_list in rm_polygon_idx_2d:
        for rm_idx, shapefile in zip(rm_idx_list,shapefile_list):
            shapefile.drop(rm_idx,inplace=True)

    # save to files
    for shapefile, shp_path in zip(shapefile_list,shp_list):
        output  = io_function.get_name_by_adding_tail(shp_path,'rmTimeiou')
        basic.outputlogMessage('remove %d polygons based on monotonically increasing time_iou, remain %d ones saving to %s' %
                                                      (remove_count, len(shapefile.geometry.values), output))
        shapefile.to_file(output, driver='ESRI Shapefile')

    return True

def main(options, args):

    # shapefile shoring polgyons for oldest to newest
    polyon_shps_list = [item for item in args]
    # print(polyon_shps_list)


    para_file = options.para_file

    # check projection of the shape file, should be the same
    new_shp_proj4 = map_projection.get_raster_or_vector_srs_info_proj4(polyon_shps_list[0])
    for idx in range(len(polyon_shps_list)-1):
        shp_proj4 = map_projection.get_raster_or_vector_srs_info_proj4(polyon_shps_list[ idx+1 ])
        if shp_proj4 != new_shp_proj4:
            raise ValueError('error, projection insistence between %s and %s'%(new_shp_proj4, shp_proj4))

    remove_non_active_thaw_slumps(polyon_shps_list,para_file)


if __name__ == "__main__":
    usage = "usage: %prog [options] polygons1.shp polygon2.shp ... (from oldest to newest) "
    parser = OptionParser(usage=usage, version="1.0 2020-02-22")
    parser.description = 'Introduction: remove polygons (e.g., non-active polygons) based on multi-temporal polygons '

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

    basic.setlogfile('polygons_remove_nonActiveRTS.log')

    main(options, args)