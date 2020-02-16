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

# sys.path.insert(0, os.path.dirname(__file__))

def calculate_overlap(polygon, series_polygons):

    # get the percent
    # add IOU to shapefile file

    pass

def get_polygon_union_same_loc(polygons_list_2d):
    '''
    get union of multi-temporal polygons at the same location
    :param polygons_list_2d: 2D list of polygons, from oldest to newest
    :return:
    '''
    union_polygons_list = []


    return union_polygons_list


def cal_multi_temporal_iou_and_occurrence(shp_list,para_file):
    '''
    calculate the IOU values of mapping polygons and their occurrence at the location across time
    IOU is based on current polygon and the union of multi-temporal polygons at the same location.
    :param shp_list: a list of shapefile, from oldest to newest
    :param para_file: para file list
    :return: the result will be saved in the shape files
    '''

    # ready polygons to 2D list
    polygons_list_2d = []
    for idx, shp in enumerate(shp_list):
        basic.outputlogMessage('read polygons from %dth shape file'%idx)
        polygons = vector_gpd.read_polygons_gpd(shp)
        polygons_list_2d.append(polygons)

    # get union of polygons at the same location
    union_polygons = get_polygon_union_same_loc(polygons_list_2d)

    # calculate IOU values and  the occurrence
    for idx, shp in enumerate(shp_list):

        polygons = polygons_list_2d[idx]
        iou_list = []
        for polygon in polygons:
            iou_value = vector_features.max_IoU_score(polygon, union_polygons)
            iou_list.append(iou_value)

        shp_obj = shape_opeation()
        shp_obj.add_one_field_records_to_shapefile(shp, iou_list, 'time_iou')

        basic.outputlogMessage('Save IOU values based on multi-temporal polygons to %s' % shp)





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
            raise ValueError('error, projection insistence between %s and %s'%(new_shp_proj4, old_shp_proj4))

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




