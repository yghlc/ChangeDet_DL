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


def get_main_shp_name(old_shp_path,new_shp_path):

    curr_dir = os.getcwd()
    folder_name = os.path.basename(curr_dir)

    import re
    # for the cases of manual delineation
    year_month_old = re.findall('\d{6}',os.path.basename(old_shp_path))
    year_month_new = re.findall('\d{6}', os.path.basename(new_shp_path))
    if len(year_month_old) == 1 and len(year_month_new) == 1:
        main_shp_name = folder_name + '_T_'+ year_month_old[0]+'_vs_'+year_month_new[0]  + '.shp'
        return main_shp_name

    # for the cases of auto mapping results
    I_num_old = re.findall('I\d+', os.path.basename(old_shp_path))
    I_num_new = re.findall('I\d+', os.path.basename(new_shp_path))
    if len(I_num_old) == 1 and len(I_num_new) == 1:
        main_shp_name = folder_name + '_T_'+ I_num_old[0]+'_vs_'+I_num_new[0]  + '.shp'
        return main_shp_name

    # for other case
    main_shp_name = os.path.splitext(os.path.basename(old_shp_path))[0] + '_' \
                    + os.path.splitext(os.path.basename(new_shp_path))[0] + '.shp'
    # short the file name if too long
    if len(main_shp_name) > 30:
        main_shp_name = os.path.splitext(os.path.basename(old_shp_path))[0][:15] + '_' \
                        + os.path.splitext(os.path.basename(new_shp_path))[0][:15] + '.shp'

    return main_shp_name

def get_expanding_change(old_shp_path,new_shp_path,para_file):


    main_shp_name = get_main_shp_name(old_shp_path, new_shp_path)

    # conduct change detection
    output_path = 'change_' + main_shp_name

    basic.outputlogMessage('Conduct change detection on %s and %s, and the results will be saved to %s' %
                           (old_shp_path, new_shp_path, output_path))

    # get expanding and shrinking parts
    output_path_expand = 'expand_' + main_shp_name
    output_path_shrink = 'shrink_' + main_shp_name
    polygons_cd.polygons_change_detection(old_shp_path, new_shp_path, output_path_expand, output_path_shrink)

    # multi polygons to polygons, then add some information of the polygons:
    # INarea, INperimete, circularit, WIDTH, HEIGHT, ratio_w_h
    all_change_polygons = 'all_changes_' + main_shp_name
    polygons_cd.Multipolygon_to_Polygons(output_path_expand, all_change_polygons)

    all_change_polygons_backup = all_change_polygons
    ##################################################################
    # post-processing for the expanding parts, to get the real expanding part (exclude delineation errors)
    #  calcuating some more information: retreat distance, relative dem

    # remove some small polygons first, to reduce the burden of calcuating retreat distance
    min_area_thr = parameters.get_digit_parameters_None_if_absence(para_file, 'minimum_change_area', 'float')
    b_smaller = True
    if min_area_thr is not None:
        rm_area_save_shp = io_function.get_name_by_adding_tail(all_change_polygons_backup, 'rmArea')
        polygons_cd.remove_polygons(all_change_polygons, 'INarea', min_area_thr, b_smaller, rm_area_save_shp)
        all_change_polygons = rm_area_save_shp
    else:
        basic.outputlogMessage('warning, minimum_change_area is absent in the para file, skip removing polygons based on INarea')

    # remove based on circularity
    min_circularity_thr = parameters.get_digit_parameters_None_if_absence(para_file, 'minimum_change_circularity', 'float')
    if min_circularity_thr is not None:
        rm_circularity_save_shp = io_function.get_name_by_adding_tail(all_change_polygons_backup, 'rmCirc')
        polygons_cd.remove_polygons(all_change_polygons, 'circularit', min_circularity_thr, True, rm_circularity_save_shp)
        all_change_polygons = rm_circularity_save_shp
    else:
        basic.outputlogMessage('warning, minimum_change_circularity is absent in the para file, skip removing polygons based on circularity')

    # added relative elevation
    dem_file = parameters.get_string_parameters_None_if_absence(para_file, 'dem_file')
    if dem_file is None:
        basic.outputlogMessage('Warning, dem_file is None, skip calculating relative dem')
    else:
        cal_relative_dem(all_change_polygons, old_shp_path, dem_file, nodata=0)

    # remove based on relative elevation
    min_relative_ele_thr = parameters.get_digit_parameters_None_if_absence(para_file, 'minimum_relative_elevation','float')
    if min_relative_ele_thr is not None:
        rm_rela_dem_save_shp = io_function.get_name_by_adding_tail(all_change_polygons_backup, 'rmRelDEM')
        polygons_cd.remove_polygons(all_change_polygons, 'diff_dem', min_relative_ele_thr, True, rm_rela_dem_save_shp)
        all_change_polygons = rm_rela_dem_save_shp
    else:
        basic.outputlogMessage(
            'warning, minimum_relative_elevation is absent in the para file, skip removing polygons based on relative DEM')

    # added retreat distance (from medial axis)  # very time-consuming
    cal_expand_area_distance(all_change_polygons)


    min_retreat_dis_thr = parameters.get_digit_parameters_None_if_absence(para_file, 'minimum_retreat_distance', 'float')
    if min_retreat_dis_thr is not None:
        rm_retreat_dis_save_shp = io_function.get_name_by_adding_tail(all_change_polygons_backup, 'rmretreatDis')
        polygons_cd.remove_polygons(all_change_polygons, 'e_max_dis', min_retreat_dis_thr, True, rm_retreat_dis_save_shp)
        all_change_polygons = rm_retreat_dis_save_shp
    else:
        basic.outputlogMessage(
            'warning, minimum_retreat_distance is absent in the para file, skip removing polygons based on the maximum retreat distance')

    # copy to output_path
    io_function.copy_shape_file(all_change_polygons,output_path)

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




