#!/usr/bin/env python
# Filename: polygons_cd 
"""
introduction: change detection for two groups of polygons (in two shape files)

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 05 January, 2020
"""

import sys,os
from optparse import OptionParser

# added path of DeeplabforRS
sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import basic_src.io_function as io_function
import basic_src.basic as basic
import basic_src.map_projection as map_projection

import vector_gpd

import pandas as pd

# for polygon comparison


def polygons_change_detection(old_shp_path, new_shp_path,save_path):
    '''
    change detection of polygons, compare their extent changes
    :param old_shp_path: the path of the old polygons
    :param new_shp_path: the path of the new polygons
    :param save_path: save path
    :return: True if successfully, False otherwise
    '''
    # check projection of the shape file, should be the same
    new_shp_proj4 = map_projection.get_raster_or_vector_srs_info_proj4(new_shp_path)
    old_shp_proj4 = map_projection.get_raster_or_vector_srs_info_proj4(old_shp_path)
    if new_shp_proj4 != old_shp_proj4:
        raise ValueError('error, projection insistence between %s and %s'%(new_shp_proj4, old_shp_proj4))

    # read old polygons as shapely objects
    old_polygons = vector_gpd.read_polygons_gpd(old_shp_path)
    if len(old_polygons) < 1:
        raise ValueError('No polygons in %s' % old_shp_path)

    old_polygon_absent = [True] * len(old_polygons)
    change_type_list = []       # 1 for expanding or shrinking, 2 for new
    polygon_diff_list = []


    # read new polygons
    new_polygons = vector_gpd.read_polygons_gpd(new_shp_path)
    if len(new_polygons) < 1:
        raise ValueError('No polygons in %s'% new_shp_path)

    # compare these two groups of polygons:
    # changes include: (1) new, (2) absence, and (3) expanding or shrinking (thaw slumps)
    for idx_new, a_new_polygon in enumerate(new_polygons):

        b_is_new = True

        for idx_old, a_old_polygon in enumerate(old_polygons):

            # find expanding or shrinking parts (two polygons must have overlap)
            intersection = a_old_polygon.intersection(a_new_polygon)
            if intersection.is_empty is True:
                continue
            else:
                # hwo to decide it is expanding or shrinking?
                # for difference operation as follows, only the expanding part of a_new_polygon will be output, that is good.
                # if want to get the shrinking part, we should use a_old_polygon.difference(a_new_polygon), but thaw slumps cannot shrink
                polygon_diff = a_new_polygon.difference(a_old_polygon)
                polygon_diff_list.append(polygon_diff)
                b_is_new = False

                # indcate that this polygon is not absent
                old_polygon_absent[idx_old] = False

            # if it is new
            if b_is_new is False:
                change_type_list.append(1) # expanding or shrinking
            else:
                change_type_list.append(2)  # new

    # find absent polygons in the old set of polygons
    absent_indices = [i for i, x in enumerate(old_polygon_absent) if x == True]
    if len(absent_indices) < 1:
        basic.outputlogMessage('No polygon disappear in %s' % old_shp_path)
    else:
        absent_indices = [ value+1 for value in  absent_indices]
        basic.outputlogMessage('Disappeared Polygons in %s: (index from 1) %s' % (old_shp_path, str(absent_indices)))

    # save the polygon changes
    changes_df = pd.DataFrame({'ChangeType': change_type_list,
                       'PolygonDiff': polygon_diff_list
                      })

    wkt_string = map_projection.get_raster_or_vector_srs_info_wkt(old_shp_path)
    vector_gpd.save_polygons_to_files(changes_df,'PolygonDiff', wkt_string, save_path)


    pass


def main(options, args):

    old_shp_path = args[0]
    new_shp_path = args[1]

    # check files do exist
    assert io_function.is_file_exist(new_shp_path)
    assert io_function.is_file_exist(old_shp_path)

    # conduct change detection
    if options.output is None:
        output_path = 'change_'+ os.path.splitext(os.path.basename(old_shp_path))[0] + '_' \
                      + os.path.splitext(os.path.basename(new_shp_path))[0] + '.shp'
    else:
        output_path = options.output

    basic.outputlogMessage('Conduct change detection on %s and %s, and the results will be saved to %s'%
                           (old_shp_path, new_shp_path, output_path))
    polygons_change_detection(old_shp_path, new_shp_path, output_path)




if __name__ == "__main__":
    usage = "usage: %prog [options] old_shape_file new_shape_file "
    parser = OptionParser(usage=usage, version="1.0 2020-01-05")
    parser.description = 'Introduction: conduct change detection for two groups of polygons '

    # parser.add_option("-p", "--para",

    #                   action="store", dest="para_file",
    #                   help="the parameters file")
    parser.add_option('-o', '--output',
                      action="store", dest = 'output',
                      help='the path to save the change detection results')

    (options, args) = parser.parse_args()
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(2)

    ## set parameters files
    # if options.para_file is None:
    #     print('error, no parameters file')
    #     parser.print_help()
    #     sys.exit(2)
    # else:
    #     parameters.set_saved_parafile_path(options.para_file)
    basic.setlogfile('polygons_changeDetection.log')

    main(options, args)



