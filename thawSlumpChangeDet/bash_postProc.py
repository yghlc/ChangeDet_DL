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
from polygon_post_process import cal_add_area_length_of_polygon
from vector_features import shape_opeation

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

def merge_raster_to_shapefile(inf_dir,save_path):

    if os.path.isfile(save_path):
        basic.outputlogMessage('%s exists, skip'%save_path)
        return True

    # curr_dir = os.getcwd()

    # os.chdir(inf_dir)

    merged_path = os.path.join(inf_dir,'merged_change_map.tif')
    if os.path.isfile(merged_path) is False:
        command_string = 'gdal_merge.py -init 0 -n 0 -a_nodata 0 -o %s %s/predict_change_map_*.tif' % (merged_path,inf_dir)
        output = os.system(command_string)
        if output != 0:
            sys.exit(1)  # this can help exit the bash script
    else:
        basic.outputlogMessage("%s exists, skip"%merged_path)

    # convert the shapefile
    # to shape files
    command_string = 'gdal_polygonize.py -8 %s -b 1 -f "ESRI Shapefile" %s'%(merged_path,save_path)
    print(command_string)
    output = os.system(command_string)
    if output != 0:
        sys.exit(1)  # this can help exit the bash script

    # os.chdir(curr_dir)

    return True

def remove_polygons(shapefile,field_name, threshold, bsmaller,output):
    '''
    remove polygons based on attribute values.
    :param shapefile: input shapefile name
    :param field_name:
    :param threshold:
    :param bsmaller:
    :param output:
    :return:
    '''
    operation_obj = shape_opeation()
    if operation_obj.remove_shape_baseon_field_value(shapefile, output, field_name, threshold, smaller=bsmaller) is False:
        return False

############################################################
## convert change map (raster) to shape file, one by one
## then merge the shapefiles. (a problem: have duplicated polygons)
# change_shp_list = []
# with open(img_pair_txt,'r') as f_obj:
#     lines = f_obj.readlines()
#     for idx, str_line in enumerate(lines):
#         # path_str [old_image, new_image, label_path (if available)]
#         path_str = [os.path.join(root, item.strip()) for item in str_line.split(':')]
#
#         # post_processing_one_change_map, set no change pixels (0) as no data
#         change_polygons_shp = post_processing_one_change_map(idx, nodata=0)
#         change_shp_list.append(change_polygons_shp)
#
#     pass
#
# # merge the shape file to a single one
# save_path = os.path.join(inf_result_dir,'predict_change_polygons.shp')
# if merge_shape_files(change_shp_list,save_path) is True:
#     basic.outputlogMessage("save change polygons to %s"%save_path)
# else:
#     basic.outputlogMessage("error, saving change polygons failed")

############################################################
# merge the raster first, then convert them to shapefiles
change_polygons_shp = os.path.join(inf_result_dir,'predict_change_polygons.shp')
merge_raster_to_shapefile(inf_result_dir,change_polygons_shp)

#

if cal_add_area_length_of_polygon(change_polygons_shp) is False:
    sys.exit(1)

# remove small polygons
area_thr = parameters.get_digit_parameters_None_if_absence(para_file,'minimum_area','int')
b_smaller = True
if area_thr is not None:
    rm_area_save_shp = io_function.get_name_by_adding_tail(change_polygons_shp, 'rmArea')
    if remove_polygons(change_polygons_shp, 'INarea', area_thr, b_smaller, rm_area_save_shp) is False:
        basic.outputlogMessage("error, removing polygons based on size failed")
    else:
        polygons_shp = rm_area_save_shp
else:
    basic.outputlogMessage('warning, minimum_area is absent in the para file, skip removing polygons based on areas')



# calculate IOU values (need validation polygons)






