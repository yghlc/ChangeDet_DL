#!/usr/bin/env python
# Filename: bash_postProc 
"""
introduction: conduct post-processing after change detection, such as polygonizing and removing small polygons

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 08 June, 2020
"""


import os,sys
sys.path.insert(0,os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))

import parameters
import basic_src.io_function as io_function

# get parameter
para_file=sys.argv[1]
if os.path.isfile(para_file) is False:
    raise IOError('File %s not exists in current folder: %s'%(para_file, os.getcwd()))

cd_dir=os.path.expanduser('~/codes/PycharmProjects/ChangeDet_DL')

# convert all the images to shape files
root=os.getcwd()
img_pair_txt=os.path.join(root,'pair_images_list.txt')
inf_result_dir = parameters.get_string_parameters(para_file, 'inf_result_dir')


def post_processing_one_change_map(idx, output_dir):

    # get the results

    # to shape files
    command_string = "gdal_polygonize.py -8 "

    output = os.system(command_string)
    if output != 0:
        sys.exit(1)  # this can help exit the bash script

    # merge the shape file to a single one

    # remove small polygons

    # calculate IOU values (need validation polygons)


with open(img_pair_txt,'r') as f_obj:


    lines = f_obj.readlines()
    for str_line in lines:
        # path_str [old_image, new_image, label_path (if available)]
        path_str = [os.path.join(root, item.strip()) for item in str_line.split(':')]

        # post_processing_one_change_map

    pass







