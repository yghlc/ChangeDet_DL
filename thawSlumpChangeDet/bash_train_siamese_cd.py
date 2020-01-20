#!/usr/bin/env python
# Filename: train the siamese neural network for change detection
"""
introduction:

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 20 January, 2020
"""


import os,sys
sys.path.insert(0,os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))

import parameters

# get parameter
para_file=sys.argv[1]
if os.path.isfile(para_file) is False:
    raise IOError('File %s not exists in current folder: %s'%(para_file, os.getcwd()))

cd_dir=os.path.expanduser('~/codes/PycharmProjects/ChangeDet_DL')
train_scrpt = os.path.join(cd_dir, 'thawSlumpChangeDet', 'siamese_thawslump_cd.py')


#run training on Cryo Station
root=os.getcwd()
img_pair_txt=os.path.join(root,'pair_images_changemap_list.txt')


batch_size = parameters.get_string_parameters(para_file, 'batch_size')
expr_name = parameters.get_string_parameters(para_file, 'expr_name')
num_epochs = parameters.get_string_parameters(para_file, 'num_epochs')
num_workers = parameters.get_string_parameters(para_file, 'num_workers')
save_frequency = parameters.get_string_parameters(para_file, 'save_frequency')


learning_rate = parameters.get_string_parameters(para_file, 'base_learning_rate')
weight_decay = parameters.get_string_parameters(para_file, 'weight_decay')

if os.path.isdir(expr_name):
    print('%s already exists, backup it'%expr_name)
    import glob
    backups = glob.glob(expr_name + '_[0-9]*')
    if len(backups) < 1:
        os.rename(expr_name, expr_name +'_1')
    else:
        os.rename(expr_name, expr_name + '_%d'%(len(backups) + 1))

os.mkdir(expr_name)

# trianing and validation
#python ${co_dir}/thawSlumpChangeDet/siamese_thawslump_cd.py ${root} ${img_pair_txt} --dotrain \
#-b ${batch_size} -l ${learning_rate} -w ${weight_decay} -e ${num_epochs} -s ${save_frequency} -n ${num_workers}

command_string = train_scrpt + ' ' + root + ' ' + img_pair_txt + ' ' + '--dotrain'  + \
' -b ' +  batch_size + ' -l ' + learning_rate + ' -w ' +  weight_decay + ' -e '  + num_epochs + \
' -s ' + save_frequency + ' -n '  +  num_workers + ' -d ' + expr_name


os.system(command_string )

#
# # prediction:
# batch_size=256
# num_workers=16
# python ${co_dir}/thawSlumpChangeDet/siamese_thawslump_cd.py ${root} ${img_pair_txt} \
# -b ${batch_size} -n ${num_workers}



