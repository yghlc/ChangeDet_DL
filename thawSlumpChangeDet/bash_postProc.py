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
cd_dir=os.path.expanduser('~/codes/PycharmProjects/ChangeDet_DL')
sys.path.insert(0,cd_dir)

import parameters
import basic_src.io_function as io_function
import basic_src.basic as basic

from dataTools.merge_shapefiles import merge_shape_files

# get parameter
para_file=sys.argv[1]
if os.path.isfile(para_file) is False:
    raise IOError('File %s not exists in current folder: %s'%(para_file, os.getcwd()))



# convert all the images to shape files
root=os.getcwd()

# image pair for change detections (prediction)
img_pair_txt=os.path.join(root,'pair_images_list.txt')

# images pairs and change polygons for training
changeDet_training_txt=os.path.join(root,'changeDet_multi_training_files.txt')
inf_result_dir = parameters.get_string_parameters(para_file, 'inf_result_dir')


def post_processing_one_change_map(idx, nodata=None):

    # get the results
    change_map_tifs = io_function.get_file_list_by_pattern(inf_result_dir,'*_%d.tif'%idx)
    if len(change_map_tifs) != 1:
        raise ValueError("more than one tif (*%d.tif) in %s"%(idx, inf_result_dir))

    change_map_tif = change_map_tifs[0]


    shp_dir = os.path.join(inf_result_dir, os.path.splitext(os.path.basename(change_map_tif))[0])
    out_shp = os.path.join(shp_dir,'%d.shp'%idx)
    if os.path.isfile(out_shp):
        basic.outputlogMessage("%s exists, skip"%out_shp)
        return out_shp

    io_function.mkdir(shp_dir)

    #set no change pixels (0) as no data
    if nodata is not None:
        command_string = 'gdal_edit.py -a_nodata %d %s' % (nodata, change_map_tif)
        output = os.system(command_string)
        if output != 0:
            sys.exit(1)  # this can help exit the bash script

    # to shape files
    command_string = 'gdal_polygonize.py -8 %s -b 1 -f "ESRI Shapefile" %s'%(change_map_tif,out_shp)
    print(command_string)
    output = os.system(command_string)
    if output != 0:
        sys.exit(1)  # this can help exit the bash script

    return out_shp

# convert change map (raster) to shape file, one by one
change_shp_list = []
with open(img_pair_txt,'r') as f_obj:
    lines = f_obj.readlines()
    for idx, str_line in enumerate(lines):
        # path_str [old_image, new_image, label_path (if available)]
        path_str = [os.path.join(root, item.strip()) for item in str_line.split(':')]

        # post_processing_one_change_map, set no change pixels (0) as no data
        change_polygons_shp = post_processing_one_change_map(idx, nodata=0)
        change_shp_list.append(change_polygons_shp)

    pass

# merge the shape file to a single one
save_path = os.path.join(inf_result_dir,'predict_change_polygons.shp')
if merge_shape_files(change_shp_list,save_path) is True:
    basic.outputlogMessage("save change polygons to %s"%save_path)
else:
    basic.outputlogMessage("error, saving change polygons failed")

# remove small polygons

# calculate IOU values (need validation polygons)






