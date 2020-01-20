#!/usr/bin/env python
# Filename: prediction the change map of two input images using Siamese Neural Network
"""
introduction:

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 20 January, 2020
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
train_scrpt = os.path.join(cd_dir, 'thawSlumpChangeDet', 'siamese_thawslump_cd.py')


#run training on Cryo Station
root=os.getcwd()
img_pair_txt=os.path.join(root,'pair_images_list.txt')


batch_size = parameters.get_string_parameters(para_file, 'batch_size')
expr_name = parameters.get_string_parameters(para_file, 'expr_name')

inf_num_workers = parameters.get_string_parameters(para_file, 'inf_num_workers')
inf_model_path = parameters.get_string_parameters(para_file, 'inf_model_path')
inf_result_dir = parameters.get_string_parameters(para_file, 'inf_result_dir')


if os.path.isdir(expr_name) is False:
    print('training folder %s does not exist'%expr_name)
    sys.exit(1)

inf_model_path = os.path.join(expr_name, inf_model_path)

if os.path.isfile(inf_model_path) is False:
    print('trained model %s does not exist'%inf_model_path)
    sys.exit(1)

if os.path.isdir(inf_result_dir):
    print('%s exists, will remove it'%inf_result_dir)
    io_function.delete_file_or_dir(inf_result_dir)

# due to the large file size, it's necessary to split them before prediction


command_string = train_scrpt + ' ' + root + ' ' + img_pair_txt + ' ' + \
' -b ' +  batch_size + ' -n '  +  inf_num_workers + ' -d ' + expr_name + \
' -m ' + inf_model_path + ' -p ' + inf_result_dir


output = os.system(command_string )
if output != 0:
    sys.exit(1)  # this can help exit the bash script

