#!/usr/bin/env python
# Filename: bash_cd_training_images 
"""
introduction: to generate training images for change detection

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 20 January, 2020
"""

import os,sys
sys.path.insert(0,os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))

import parameters

cd_dir=os.path.expanduser('~/codes/PycharmProjects/ChangeDet_DL/dataTools')
get_subImg_pair_scrpt = os.path.join(cd_dir, 'get_subimage_pairs.py')

# get parameter
para_file=sys.argv[1]
if os.path.isfile(para_file) is False:
    raise IOError('File %s not exists in current folder: %s'%(para_file, os.getcwd()))


dstnodata = parameters.get_string_parameters(para_file, 'dst_nodata')
buffer_size = parameters.get_string_parameters(para_file, 'buffer_size')
b_use_rectangle = parameters.get_string_parameters(para_file, 'b_use_rectangle')
multi_training_files = parameters.get_string_parameters(para_file, 'multi_training_files')
out_dir = os.getcwd()

def get_subImg_pair_one_shp(buffersize, dstnodata, rectangle_ext, train_shp, old_image_folder, new_image_folder, out_dir, file_pattern = None):
    if file_pattern is None:
        file_pattern = '*.tif'

    command_string = get_subImg_pair_scrpt + ' -b ' + str(buffersize) + ' -e ' + file_pattern + \
                    ' -o ' + out_dir + ' -n ' + str(dstnodata) + ' ' + rectangle_ext + ' ' + \
                     train_shp + ' '+ old_image_folder + ' '+ new_image_folder

    # ${eo_dir}/sentinelScripts/get_subImages.py -f ${all_train_shp} -b ${buffersize} -e .tif \
    #             -o ${PWD} -n ${dstnodata} -r ${train_shp} ${input_image_dir}

    # status, result = basic.exec_command_string(command_string)  # this will wait command finished
    # os.system(command_string + "&")  # don't know when it finished
    output = os.system(command_string )      # this work
    # print(output)
    if output != 0:
        sys.exit(1)  # this can help exit the bash script


with open(multi_training_files, 'r') as f_obj:
    lines = f_obj.readlines()

    for line in lines:
        old_image_folder, new_image_folder, file_pattern, change_shp = line.strip().split(':')
        # print(old_image_folder, new_image_folder, file_patter, change_shp)
        get_subImg_pair_one_shp(buffer_size,dstnodata,b_use_rectangle,change_shp,
                                old_image_folder,new_image_folder,out_dir,file_pattern=file_pattern)




