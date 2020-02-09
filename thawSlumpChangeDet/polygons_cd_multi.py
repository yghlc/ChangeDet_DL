#!/usr/bin/env python
# Filename: polygon_based_ChangeDet 
"""
introduction: run polygons based change detection for a seires of multi-temporal images

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 09 February, 2020
"""

import sys,os
from optparse import OptionParser

# added path of DeeplabforRS
sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import basic_src.basic as basic
import basic_src.io_function as io_function
import basic_src.map_projection as map_projection

import parameters

# sys.path.insert(0, os.path.dirname(__file__))
import polygons_cd
from cal_relative_dem import cal_relative_dem
from cal_retreat_rate import cal_expand_area_distance

def get_expanding_change(old_shp_path,new_shp_path,para_file):

    main_shp_name = os.path.splitext(os.path.basename(old_shp_path))[0] + '_' \
                    + os.path.splitext(os.path.basename(new_shp_path))[0] + '.shp'
    # short the file name if too long
    if len(main_shp_name) > 60:
        main_shp_name = os.path.splitext(os.path.basename(old_shp_path))[0][:30] + '_' \
                        + os.path.splitext(os.path.basename(new_shp_path))[0][:30] + '.shp'

    # conduct change detection
    output_path = 'change_' + main_shp_name

    basic.outputlogMessage('Conduct change detection on %s and %s, and the results will be saved to %s' %
                           (old_shp_path, new_shp_path, output_path))

    # get expanding and shrinking parts
    output_path_expand = 'expand_' + main_shp_name
    output_path_shrink = 'shrink_' + main_shp_name
    polygons_cd.polygons_change_detection(old_shp_path, new_shp_path, output_path_expand, output_path_shrink)

    # multi polygons to polygons, then add some information on the polygons
    all_change_polygons = 'all_changes_' + main_shp_name
    polygons_cd.Multipolygon_to_Polygons(output_path_expand, all_change_polygons)

    # added retreat distance (from medial axis)
    cal_expand_area_distance(all_change_polygons)

    # added relative elevation
    dem_file = parameters.get_string_parameters_None_if_absence(para_file, 'dem_file')
    if dem_file is None:
        basic.outputlogMessage('Warning, dem_file is None, skip calculating relative dem')
    else:
        cal_relative_dem(all_change_polygons, old_shp_path, dem_file, nodata=0)

    # # post-processing of the expanding parts, to get the real expanding part (exclude delineation errors)
    min_area_thr = parameters.get_digit_parameters_None_if_absence(para_file, 'minimum_change_area', 'float')
    min_circularity_thr = parameters.get_digit_parameters_None_if_absence(para_file,'minimum_change_circularity', 'float')
    min_retreat_dis_thr = parameters.get_digit_parameters_None_if_absence(para_file,'minimum_retreat_distance', 'float')
    min_relative_ele_thr = parameters.get_digit_parameters_None_if_absence(para_file,'minimum_relative_elevation', 'float')

    polygons_cd.expanding_change_post_processing(all_change_polygons, output_path, min_area_thr, min_circularity_thr,
                                                 e_max_dis_thr=min_retreat_dis_thr, relative_dem_thr=min_relative_ele_thr)

    return True

def main(options, args):

    # for oldest to newest
    polyon_shps_list = [item for item in args]
    print(polyon_shps_list)

    para_file = options.para_file

    for idx in range(len(polyon_shps_list)-1):
        # print(idx)
        get_expanding_change(polyon_shps_list[idx], polyon_shps_list[idx+1], para_file)


    pass

if __name__ == "__main__":
    usage = "usage: %prog [options] polygons1.shp polygon2.shp ... (from oldest to newest) "
    parser = OptionParser(usage=usage, version="1.0 2020-02-09")
    parser.description = 'Introduction: conduct change detection multi-temporal polygons '

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

    # set parameters files
    if options.para_file is None:
        print('error, no parameters file')
        parser.print_help()
        sys.exit(2)
    else:
        parameters.set_saved_parafile_path(options.para_file)

    basic.setlogfile('polygons_changeDetection.log')

    main(options, args)




