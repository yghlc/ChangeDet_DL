#!/usr/bin/env python3
# Filename: polygons_cd_multi_exe
"""
introduction: run polygons based change detection in the mapping folder

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 24 February, 2020
"""

import sys,os

# added path of DeeplabforRS
sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import basic_src.basic as basic
import basic_src.io_function as io_function
import parameters

import re

cd_code=os.path.expanduser("~/codes/PycharmProjects/ChangeDet_DL")
polygons_cd_multi_py = os.path.join(cd_code,'thawSlumpChangeDet','polygons_cd_multi.py')

if __name__ == "__main__":
    para_file = sys.argv[1]
    test_name = sys.argv[2]

    import datetime
    start_time = datetime.datetime.now()

    expr_name = parameters.get_string_parameters(para_file,'expr_name')
    NUM_ITERATIONS = parameters.get_string_parameters(para_file,'export_iteration_num')
    trail= 'iter' + NUM_ITERATIONS

    curr_dir = os.getcwd()
    testid = os.path.basename(curr_dir)+'_'+expr_name+'_'+trail

    # mapping results folder
    bak_dir = os.path.join('result_backup',testid+'_'+test_name+'_tiles')

    # read shape file list
    b_remove_multi = parameters.get_bool_parameters_None_if_absence(para_file,'b_remove_polygons_using_multitemporal_results')
    if b_remove_multi is None or b_remove_multi is False:
        file_pattern = "I*_" + testid + "*post_" + test_name + ".shp"
    else:
        file_pattern = "I*_" + testid + "*post_" + test_name + "_rmTimeiou.shp"

    polygon_shps_list = io_function.get_file_list_by_pattern(bak_dir, file_pattern)
    if len(polygon_shps_list) < 2:
        raise ValueError('Error, less than two shapefiles, cannot conduct polygon-based change detection')

    # make polygon_shps_list in order: I0 to In
    polygon_shps_list.sort(key=lambda x: int(re.findall('I\d+', os.path.basename(x))[0][1:]))

    # change to absolute path, because later, we will change the running folder
    polygon_shps_list = [os.path.abspath(item) for item in polygon_shps_list]

    # change detection folder
    out_dir = os.path.join('result_backup',testid+'_'+test_name+'_PolyChanges')
    io_function.mkdir(out_dir)

    # copy para file and change_validation_shape_list
    if io_function.copyfiletodir(para_file, out_dir,overwrite=True) is False:
        sys.exit(1)
    validate_list_txt = parameters.get_string_parameters_None_if_absence(para_file, 'change_validation_shape_list')
    if validate_list_txt is not None:
        if io_function.copyfiletodir(validate_list_txt,out_dir, overwrite=True) is False:
            sys.exit(1)


    os.chdir(out_dir)

    # conduct polygon-based change detection
    args_list = [polygons_cd_multi_py, '-p',para_file]
    for shp_path in polygon_shps_list:
        args_list.append(shp_path)

    basic.exec_command_args_list(args_list)

    end_time = datetime.datetime.now()
    diff_time = end_time - start_time
    out_str = "%s: time cost of polygon-based change detection : %d seconds" % (str(end_time), diff_time.seconds)
    basic.outputlogMessage(out_str)
    with open("time_cost.txt", 'a') as t_obj:
        t_obj.writelines(out_str + '\n')



