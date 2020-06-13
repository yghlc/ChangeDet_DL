#!/usr/bin/env python
# Filename: plot_p_r_curves 
"""
introduction: plot precision-recall curves for mapping results using multi-temporal images.

# run this script in ~/Data/Qinghai-Tibet/beiluhe/result/result_multi_temporal_changes_17-19July

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 13 June, 2020
"""

import os, sys
deeplabforRS = os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS')
sys.path.insert(0, deeplabforRS)

import parameters
import basic_src.io_function as io_function
import basic_src.basic as basic

from plot_accuracies import plot_precision_recall_curve
from plot_accuracies import plot_precision_recall_curve_multi

import matplotlib.pyplot as plt

def read_validate_shapefiles(txt_path):
    basic.outputlogMessage('read validation shapefiles from %s'%txt_path)
    shp_list = []
    with open(txt_path,'r') as f_obj:
        shp_list_tmp =  [ line.strip() for line in f_obj.readlines()]

        # the shapefile's existence, change file path if necessary
        for tmp in shp_list_tmp:
            tmp_str = tmp.split('/')
            new_tmp = '~/'+'/'.join(tmp_str[3:])
            print(new_tmp)
            new_shp_path = os.path.expanduser(new_tmp)
            if io_function.is_file_exist(new_shp_path):
                shp_list.append(new_shp_path)

    return shp_list


def draw_precision_recall_curves(shp_paths,ground_truth_shp,out_fig_path, legend_loc='best'):
    # plot precision recall curves for mapping result of one images (one validation shape file)

    if isinstance(shp_paths,list) and len(shp_paths) > 1:
        plot_precision_recall_curve_multi(shp_paths, ground_truth_shp, out_fig_path,legend_loc=legend_loc)
    else:
        if isinstance(shp_paths, list):
            shape_file = shp_paths[0]
        else:
            shape_file = shp_paths
        plot_precision_recall_curve(shape_file, ground_truth_shp, out_fig_path)
    return True


def draw_p_r_curves_one_k_fold(k_value, test_num,image_count=1,res_description = 'post',legend_loc='best'):

    # 5fold_test3
    res_dir = '%dfold_test%d'%(k_value,test_num)

    multi_validate_shapefile_txt = io_function.get_file_list_by_pattern(res_dir,'*_tiles/multi_validate_shapefile.txt')
    multi_validate_shapefiles = read_validate_shapefiles(multi_validate_shapefile_txt[0])
    if len(multi_validate_shapefiles) != image_count:
        raise ValueError('the count of validation shapefiles and images is different')

    for img_idx in range(image_count):
        # for the result after post-procesing (without appling remove non-active thaw slump using multi-temporal image)
        save_fig_path = 'I%d_p_r_%s_%s.jpg' % (img_idx, res_dir, res_description)
        if os.path.isfile(save_fig_path):
            basic.outputlogMessage('warning, %s exists, skip'%save_fig_path)
            continue
        if res_description == 'post':
            shps_list = io_function.get_file_list_by_pattern(res_dir,'*_tiles/I%d_*post*t%d.shp'%(img_idx,test_num))
            draw_precision_recall_curves(shps_list, multi_validate_shapefiles[img_idx], save_fig_path,legend_loc=legend_loc)

        elif res_description == 'rmTimeiou':
            shps_list = io_function.get_file_list_by_pattern(res_dir, '*_tiles/I%d_*post*rmTimeiou.shp' % (img_idx))
            draw_precision_recall_curves(shps_list, multi_validate_shapefiles[img_idx], save_fig_path,legend_loc=legend_loc)

        else:
            raise ValueError('Unknown result description (e.g., post, rmTimeiou)')

        # plt.clf()   # clears the entire current figure with all its axes, but leaves the window opened for next plot
        plt.close()
        # for test
        # sys.exit(1)
    pass


def draw_p_r_curves_for_all_k_fold_test():

    curr_dir = os.getcwd()

    # plot precision-recall curves for k-fold cross-validation
    os.chdir('k_fold_cross_validation')

    for k in (3,5,10):
        for test_num in range(1,6):
            print(k, test_num)
            # for image from 2017 to 2019 (count = 3)
            draw_p_r_curves_one_k_fold(k, test_num, image_count=3, res_description='post')

            draw_p_r_curves_one_k_fold(k, test_num, image_count=3, res_description='rmTimeiou', legend_loc='upper left')


    os.chdir(curr_dir)




if __name__ == "__main__":

    basic.setlogfile('plot_p_r_curves.log')

    # draw precission recall for all k-fold cross-validation
    draw_p_r_curves_for_all_k_fold_test()


    pass

