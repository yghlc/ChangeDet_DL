#!/usr/bin/env python
# Filename: merge_neg_pos_polygons 
"""
introduction: Merge ground truths and negative training polygons, to obtain training polygons containg both positive and negative polygons

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 01 September, 2020
"""


import os, sys
sys.path.insert(0,os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import vector_gpd
import basic_src.io_function as io_function
import basic_src.basic as basic

from basic_src.map_projection import get_raster_or_vector_srs_info_proj4

import pandas as pd
from optparse import OptionParser

def merge_pos_neg_polygons_files(pos_polygon_shp, neg_polygon_shp, save_path):
    '''
    merge negative and positive training polygons
    :param pos_polygon_shp:
    :param neg_polygon_shp:
    :param save_path:
    :return:
    '''

    assert io_function.is_file_exist(pos_polygon_shp)

    pos_prj = get_raster_or_vector_srs_info_proj4(pos_polygon_shp)

    pos_polygons = vector_gpd.read_polygons_gpd(pos_polygon_shp)

    # if negative file not exit, copy the positive directly
    neg_polygons = []
    if os.path.isfile(neg_polygon_shp):
        neg_prj = get_raster_or_vector_srs_info_proj4(neg_polygon_shp)
        if pos_prj != neg_prj:
            raise ValueError('Projection inconsistent between %s and %s'%(pos_polygon_shp,neg_polygon_shp))

        neg_polygons = vector_gpd.read_polygons_gpd(neg_polygon_shp)

    save_polygon_list = []
    id_list = []
    class_int_list = []

    id = 0
    for poly in pos_polygons:
        save_polygon_list.append(poly)
        id_list.append(id + 1)
        id += 1
        class_int_list.append(1)    # positive

    for poly in neg_polygons:
        save_polygon_list.append(poly)
        id_list.append(id + 1)
        id += 1
        class_int_list.append(0)    # negative

    # save results
    save_polyons_attributes = {'id':id_list,
                               'class_int':class_int_list,
                               "Polygons":save_polygon_list}

    polygon_df = pd.DataFrame(save_polyons_attributes)
    return vector_gpd.save_polygons_to_files(polygon_df, 'Polygons', pos_prj, save_path)


def main(options, args):

    if len(args) == 1:
        pos_polygon_shp = args[0]
        neg_polygon_shp = ""
    elif len(args) == 2:
        pos_polygon_shp = args[0]
        neg_polygon_shp = args[1]
    else:
        raise ValueError('incorrect input')

    out_shp = options.output

    basic.outputlogMessage('input ground truths: %s' % pos_polygon_shp)
    basic.outputlogMessage('input negative training polygons: %s' % neg_polygon_shp)

    if merge_pos_neg_polygons_files(pos_polygon_shp,neg_polygon_shp,out_shp):
        basic.outputlogMessage('save to %s'%out_shp)

    pass

if __name__ == "__main__":
    usage = "usage: %prog [options] pos_shp neg_shp "
    parser = OptionParser(usage=usage, version="1.0 2020-09-01")
    parser.description = 'Introduction: merge positive and negative training polygons '

    # parser.add_option("-p", "--para",
    #                   action="store", dest="para_file",
    #                   help="the parameters file")

    parser.add_option('-o', '--output',
                      action="store", dest = 'output',
                      help='the path to save output shape file ')

    (options, args) = parser.parse_args()

    if len(args) < 1:
        parser.print_help()
        sys.exit(2)

    # set output file
    if options.output is None:
        print('error, no output file')
        parser.print_help()
        sys.exit(2)

    main(options, args)


    pass