#!/usr/bin/env python
# Filename: polygons_change_analyze
"""
introduction: run polygons based change analysis for a series of multi-temporal polygons (from manual delineation or automatic mapping)

try to output info that indicates that IOU values of mapping polygons and their occurrence at the location across time
IOU is based on current polygon and the union of multi-temporal polygons at the same location.


authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 15 February, 2020
"""

import sys,os
from optparse import OptionParser

# added path of DeeplabforRS
sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import basic_src.basic as basic
import basic_src.map_projection as map_projection

import parameters
import vector_gpd
import vector_features
from vector_features import shape_opeation

import pandas as pd

# sys.path.insert(0, os.path.dirname(__file__))

def get_a_polygon_union_occurrence(polygon, polygons_list_2d, b_merged_2d, time_idx, time_num):
    '''
    for a input polygon, based on it to get a union and occurences
    :param polygon: a polygon
    :param polygons_list_2d: 2D list of polygons, from oldest to newest
    :param b_merged_2d: indicate a polygon has been merged into union
    :param time_idx: time index
    :param time_num: the count of multi-temporal polygons
    :return:
    '''

    union_polygon = polygon
    occurrence = 1
    occur_time = [time_idx]

    # # from t_0 to t_n, except time_idx, we suppose that the thaw slump change gradually,
    # # the same polygons of thaw slumps at different time cannot jump suddenly
    # for t_idx in range(time_num):
    #     # skip time_idx
    #     if t_idx == time_idx:
    #         continue
    #
    #     for idx, t_polygon in enumerate(polygons_list_2d[t_idx]):
    #         # if it already be merged to other polygons, then skip it
    #         if b_merged_2d[t_idx][idx]:
    #             continue
    #
    #         intersection = union_polygon.intersection(t_polygon)
    #         if intersection.is_empty:
    #             continue
    #         else:
    #             union_polygon = union_polygon.union(t_polygon)
    #             b_merged_2d[t_idx][idx] = True          # marked it
    #             occurrence += 1
    #
    #             # in one group of polygons (at the same time), only have one intersection polygon,
    #             # otherwise, something wrong with the mapping results
    #             # break

    # need to get the union polygon in a Recursive Way
    found_new_polygon = True
    while found_new_polygon:

        found_new_polygon = False

        for t_idx in range(time_num):
            for idx, t_polygon in enumerate(polygons_list_2d[t_idx]):
                # if it already be merged to other polygons, then skip it
                if b_merged_2d[t_idx][idx]:
                    continue

                intersection = union_polygon.intersection(t_polygon)
                if intersection.is_empty:
                    continue
                else:
                    union_polygon = union_polygon.union(t_polygon)
                    b_merged_2d[t_idx][idx] = True          # marked it
                    occurrence += 1
                    occur_time.append(t_idx)

                    found_new_polygon = True


    return union_polygon, occurrence, occur_time

def get_polygon_union_occurrence_same_loc(polygons_list_2d):
    '''
    get union of multi-temporal polygons at the same location
    :param polygons_list_2d: 2D list of polygons, from oldest to newest
    :return:
    '''
    basic.outputlogMessage('Get unions of multi-temporal polygons at the same location')
    union_polygons_list = []
    # occurrence: each union polygons consist of how many of polygons.
    occurrence_list = []
    occurrence_time_list = []   # indicate what time the polygon occur

    time_num = len(polygons_list_2d)

    # indicate a polygon has been merged into union
    b_merged_2d = []
    for polygons in polygons_list_2d:
        b_merged_2d.append([False]*len(polygons))

    for time_idx, (b_merged_1d, polygon_list) in enumerate(zip(b_merged_2d,polygons_list_2d)):
        basic.outputlogMessage('Scan polygons on Time %d'%time_idx)
        for idx in range(len(polygon_list)):
            # if this polygon has been merged to a union, then skip
            if b_merged_1d[idx]:
                continue

            # get polygon union
            based_polygon = polygon_list[idx]
            b_merged_1d[idx] = True         # mark it

            union_polygon, occurrence_count, occurrence_time = get_a_polygon_union_occurrence(based_polygon,polygons_list_2d, b_merged_2d, time_idx, time_num)
            union_polygons_list.append(union_polygon)
            occurrence_list.append(occurrence_count)
            occurrence_time_list.append(occurrence_time)

    return union_polygons_list, occurrence_list, occurrence_time_list

def max_IoU_score(polygon, polygon_list):
    """
    get the IoU score of one polygon compare to many polygon (validation polygon)
    :param polygon: the detected polygon
    :param polygon_list: a list contains training polygons
    :return: the max IoU score, False otherwise
    """
    max_iou = 0.0
    max_idx = -1
    for idx, training_polygon in enumerate(polygon_list):
        temp_iou = vector_features.IoU(polygon,training_polygon)
        if temp_iou > max_iou:
            max_iou = temp_iou
            max_idx = idx
    return max_iou, max_idx

def cal_multi_temporal_iou_and_occurrence(shp_list,para_file):
    '''
    calculate the IOU values of mapping polygons and their occurrence at the location across time
    IOU is based on current polygon and the union of multi-temporal polygons at the same location.
    :param shp_list: a list of shapefile, from oldest to newest
    :param para_file: para file list
    :return: the result will be saved in the shape files
    '''
    basic.outputlogMessage('Start calculating time_iou and occurrence')
    # ready polygons to 2D list
    polygons_list_2d = []
    for idx, shp in enumerate(shp_list):
        basic.outputlogMessage('read polygons from %dth shape file'%idx)
        polygons = vector_gpd.read_polygons_gpd(shp)
        polygons_list_2d.append(polygons)

    # get union of polygons at the same location
    union_polygons, occurrence_list, occur_time_list = get_polygon_union_occurrence_same_loc(polygons_list_2d)
    # save the polygon changes
    union_id_list = [item+1 for item in range(len(union_polygons))]
    occur_time_str_list = []
    for idx_list in occur_time_list:
        time_str = '_'.join([str(item) for item in idx_list])
        occur_time_str_list.append(time_str)
    union_save_path = 'union_of_%s.shp'%'_'.join([str(item) for item in range(len(shp_list))])

    union_df = pd.DataFrame({'id': union_id_list,
                            'time_occur': occurrence_list,
                            'time_idx': occur_time_str_list,
                            'UnionPolygon': union_polygons
                            })
    wkt_string = map_projection.get_raster_or_vector_srs_info_wkt(shp_list[0])
    vector_gpd.save_polygons_to_files(union_df, 'UnionPolygon', wkt_string, union_save_path)


    # calculate IOU values and  the occurrence
    for idx, shp in enumerate(shp_list):

        polygons = polygons_list_2d[idx]
        iou_list = []
        occurrence = []
        occurr_time = []
        for polygon in polygons:
            iou_value, max_idx = max_IoU_score(polygon, union_polygons)
            iou_list.append(iou_value)
            occurrence.append(occurrence_list[max_idx])
            occur_time_str = [str(item) for item in occur_time_list[max_idx]]
            occurr_time.append('_'.join(occur_time_str))

        shp_obj = shape_opeation()
        shp_obj.add_one_field_records_to_shapefile(shp, iou_list, 'time_iou')
        shp_obj.add_one_field_records_to_shapefile(shp, occurrence, 'time_occur')
        shp_obj.add_one_field_records_to_shapefile(shp, occurr_time, 'time_idx')


        basic.outputlogMessage('Save IOU values and occurrence based on multi-temporal polygons to %s' % shp)



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

    cal_multi_temporal_iou_and_occurrence(polyon_shps_list,para_file)



    pass

if __name__ == "__main__":
    usage = "usage: %prog [options] polygons1.shp polygon2.shp ... (from oldest to newest) "
    parser = OptionParser(usage=usage, version="1.0 2020-02-09")
    parser.description = 'Introduction: conduct change analysis on multi-temporal polygons '

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

    basic.setlogfile('polygons_changeAnalysis.log')

    main(options, args)




