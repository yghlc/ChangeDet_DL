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
import vector_gpd
import vector_features
from vector_features import shape_opeation


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
    # ready polygons to 2D list
    polygons_list_2d = []
    for idx, shp in enumerate(shp_list):
        basic.outputlogMessage('read polygons from %dth shape file'%idx)
        polygons = vector_gpd.read_polygons_gpd(shp)
        polygons_list_2d.append(polygons)

    for idx, shp_file in enumerate(new_shp_list):
        pass

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

    basic.setlogfile('polygons_changeAnalysis.log')

    main(options, args)