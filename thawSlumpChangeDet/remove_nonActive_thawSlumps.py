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

import polygons_change_analyze

def get_polygon_idx_and_time_iou(ref_polygon, shapefile_gpd):
    for idx, row in shapefile_gpd.iterrows():
        polygon = row['geometry']
        intersection = ref_polygon.intersection(polygon)
        if intersection.is_empty:
            continue
        return idx, row['time_iou'], polygon

    return None, None, None

def remove_non_active_thaw_slumps(shp_list,para_file):
    '''
    remove polygons based on information from multi-temporal polygons
    :param shp_list: a list of shapefile, from oldest to newest
    :param para_file: para file list
    :return:
    '''
    basic.outputlogMessage('Start removing polygons based on multi-temporal information')

    shp_list_copy = shp_list.copy()

    new_shp_list = []
    # remove polygons based on time occurrence ('time_occur')
    normal_occurrence = len(shp_list)       # the expected count
    min_occurrence = parameters.get_digit_parameters_None_if_absence(para_file,'minimum_time_occurence','int')
    max_occurrence = parameters.get_digit_parameters_None_if_absence(para_file,'maximum_time_occurence','int')
    for idx, shp_file in enumerate(shp_list):
        # remove occurance
        save_shp = io_function.get_name_by_adding_tail(shp_file, 'RmOccur')
        # vector_gpd.remove_polygon_equal(shp_file,'time_occur',normal_occurrence, True,save_shp)
        vector_gpd.remove_polygons_not_in_range(shp_file,'time_occur',min_occurrence,max_occurrence,save_shp)
        new_shp_list.append(save_shp)


    # remove based on time_idx
    shp_list = new_shp_list.copy()
    new_shp_list = []
    normal_time_idx = '_'.join([str(item) for item in range(normal_occurrence)])
    # normal_time_idx = [item for item in range(normal_occurrence)]
    for idx, shp_file in enumerate(shp_list):
        # remove occurance
        save_shp = io_function.get_name_by_adding_tail(shp_file, 'RmTimeidx')
        vector_gpd.remove_polygon_time_index(shp_file,'time_idx',normal_occurrence, save_shp)
        # vector_gpd.remove_polygon_equal(shp_file,'time_idx',normal_time_idx, True,save_shp)
        # vector_gpd.remove_polygon_index_string(shp_file,'time_idx',normal_time_idx,save_shp)
        new_shp_list.append(save_shp)

    shp_list = new_shp_list.copy()
    # new_shp_list = []

    ### remove polygons based on time iou ('time_iou'), as a thaw slump develop, the time_iou should be increase
    # ready time_iou to 2D list
    shapefile_list = []
    polygons_list_2d = []
    for idx, shp in enumerate(shp_list):
        shapefile = gpd.read_file(shp)

        if 'time_iou' not in shapefile.keys():
            raise ValueError('error, %s do not have time_iou, please conduct polygon_change_analyze first'%shp)
        shapefile_list.append(shapefile)
        polygons_list_2d.append(vector_gpd.fix_invalid_polygons(shapefile.geometry.values))  # read the polygons and also check the invalidity

        # print(shapefile.keys())
        # print(shapefile['time_iou'])
        # print(len(shapefile.geometry.values))

    # remove polygons the time_iou are not monotonically increasing
    # after removing polygons based on time occurrence, the polygon number in all shape file should be the same
    iou_mono_increasing_thr = parameters.get_digit_parameters_None_if_absence(para_file,'iou_mono_increasing_thr','float')
    if iou_mono_increasing_thr is None:
        iou_mono_increasing_thr = 0
        basic.outputlogMessage('Warning, iou_mono_increasing_thr not set, it will be set as 0')

    # get union of polygons at the same location
    union_polygons, occurrence_list, occur_time_list = polygons_change_analyze.get_polygon_union_occurrence_same_loc(polygons_list_2d)

    rm_polygon_idx_2d = []

    ################ read time index based on the first t0 polygon and assume all location has the same number of polygons  ####
    # time_iou_1st = shapefile_list[0]['time_iou']
    # for idx, t_iou_value_1st in enumerate(time_iou_1st): # shapefile_list[0].geometry.values
    #     # read time iou
    #     time_iou_values = [t_iou_value_1st]
    #     idx_list = [idx]
    #     polygon = shapefile_list[0].geometry.values[idx]
    #
    #     # find the union polygon
    #     cor_union_poly = None
    #     for union_poly in union_polygons:
    #         intersection = polygon.intersection(union_poly)
    #         if intersection.is_empty is False:
    #             cor_union_poly = union_poly
    #             break
    #     if cor_union_poly is None:
    #         raise ValueError('Error, The union is None')
    #
    #     # read other polygon and time_iou in other shape file
    #     for time in range(1, normal_occurrence):
    #         t_idx, t_iou, t_polygon = get_polygon_idx_and_time_iou(cor_union_poly,shapefile_list[time])
    #         time_iou_values.append(t_iou)
    #         idx_list.append(t_idx)
    #
    #     if None in idx_list:
    #         basic.outputlogMessage('Warning, None in the index list: %s '%str(idx_list))
    #         continue

    # based on each union polygons, to read time_iou, allow each location has various polygons #
    for idx, union_poly in enumerate(union_polygons):  # shapefile_list[0].geometry.values
        time_iou_values = []
        idx_list = []
        for time in range(0, normal_occurrence):
            t_idx, t_iou, t_polygon = get_polygon_idx_and_time_iou(union_poly,shapefile_list[time])
            time_iou_values.append(t_iou)
            idx_list.append(t_idx)

        # remove none value
        if None in idx_list:
            time_iou_values.remove(None)

        # check if time iou is monotonically increasing
        time_iou_array = np.array(time_iou_values, dtype=np.float64)       # specify the dtype to avoid unexpected error
        if np.all(np.diff(time_iou_array) >= iou_mono_increasing_thr):
            pass
        else:
            basic.outputlogMessage('The areas of Polygons %s : iou: %s in temporal shapefiles is not monotonically increasing, remove them'%
                                   (str(idx_list), str(time_iou_values)))
            rm_polygon_idx_2d.append(idx_list)
        # print(time_iou_values, rm_polygon_idx_2d)

    remove_count = len(rm_polygon_idx_2d)
    for rm_idx_list in rm_polygon_idx_2d:
        for rm_idx, shapefile in zip(rm_idx_list,shapefile_list):
            #         errors : {'ignore', 'raise'}, default 'raise'
            #             If 'ignore', suppress error and only existing labels are
            #             dropped.
            if rm_idx is None:
                continue
            shapefile.drop(rm_idx,inplace=True,errors='ignore')     # some rm_idx many have been dropped previously

    # save to files
    for shapefile, shp_path in zip(shapefile_list,shp_list_copy):
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