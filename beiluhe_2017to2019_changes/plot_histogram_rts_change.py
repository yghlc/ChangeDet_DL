#!/usr/bin/env python
# Filename: plot_histogram_rts_change 
"""
introduction: plot histogram of RTS change after "statistic change RTSs"

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 06 July, 2020
"""
import os, sys
import numpy as np

sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS') )

import basic_src.io_function as io_function

from plot_histogram import read_attribute
from plot_histogram import draw_one_list_histogram


#(shp_0vs1,shp_1vs2, field_name, out_pre_name, bin_min,bin_max,bin_width,ylim)

def draw_two_hist_of_cd(shp_0vs1,shp_1vs2,out_dir, field_name, out_pre_name, bin_min,bin_max,bin_width,ylim):

    draw_one_value_hist(shp_0vs1,field_name,out_dir,out_pre_name+'_2017vs2018.jpg',out_pre_name+'_2017vs2018.txt',bin_min,bin_max,bin_width,ylim)
    draw_one_value_hist(shp_1vs2,field_name,out_dir,out_pre_name+'_2018vs2019.jpg',out_pre_name+'_2018vs2019.txt',bin_min,bin_max,bin_width,ylim)

def draw_one_value_hist(shp_file,field_name,out_dir,output,logfile,bin_min,bin_max,bin_width,ylim):

    values = read_attribute(shp_file, field_name)
    if 'area' in field_name:                      # m^2 to ha
        values = [item/10000.0 for item in values]

    xlabelrotation = None
    if 'area' in field_name or 'INperimete' in field_name or 'circularit' in field_name or 'aspectLine' in field_name or \
        'dem' in field_name or 'slo_max' in field_name or 'dis' in field_name or 'poly_num' in field_name \
            or 'diff' in field_name:
        xlabelrotation = 90

    bins = np.arange(bin_min, bin_max, bin_width)

    # plot histogram of slope values
    # value_list,output,bins=None,labels=None,color=None,hatch=""
    draw_one_list_histogram(values, output,bins=bins,color=['grey'],xlabelrotation=xlabelrotation,ylim=ylim )  # ,hatch='-'
    io_function.move_file_to_dst('processLog.txt', os.path.join(out_dir, logfile), overwrite=True)
    io_function.move_file_to_dst(output, os.path.join(out_dir, output), overwrite=True)

def draw_hist_for_RTS_change_manu():

    ##########################################################################################
    # # plot histogram on RTS change (group info from one or multiple change polygons) based on manual delineation of thaw slumps in Beiluhe
    out_dir = os.path.expanduser('~/Data/Qinghai-Tibet/beiluhe/beiluhe_planet/polygon_based_ChangeDet/manu_blh_2017To2019')
    shp_dir = os.path.expanduser('~/Data/Qinghai-Tibet/beiluhe/beiluhe_planet/polygon_based_ChangeDet/manu_blh_2017To2019')
    c_RTS_info_2017vs2018_shp = os.path.join(shp_dir, 'rts_change_2017vs2018.shp')
    c_RTS_info_2018vs2019_shp = os.path.join(shp_dir, 'rts_change_2018vs2019.shp')

    # sum area
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018_shp,c_RTS_info_2018vs2019_shp,out_dir,'sum_c_area','rts_sum_area_manu_cd',0, 2.6, 0.2, [0, 145])

    # max area (the maximum (in area) change polygon for an thaw slump)
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018_shp, c_RTS_info_2018vs2019_shp, out_dir, 'max_c_area', 'rts_max_area_manu_cd', 0, 2.6, 0.2, [0, 170])

    # count of change polygons
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018_shp, c_RTS_info_2018vs2019_shp, out_dir, 'c_poly_num', 'rts_c_poly_num_manu_cd', 0, 20, 1, [0, 100])

    # maximum retreat distance (based on medial circle)
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018_shp, c_RTS_info_2018vs2019_shp, out_dir, 'max_re_dis', 'rts_max_re_dis_manu_cd', 5, 81, 5, [0, 55])

    # maxDisLin (retread distance from manual delineation)
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018_shp, c_RTS_info_2018vs2019_shp, out_dir, 'maxDisLin','rts_maxDisLin_manu_cd', 5, 81, 5, [0, 55])

    # diffDisLin (difference between maximum retreat distance based on medial circle and manually drawn line)
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018_shp, c_RTS_info_2018vs2019_shp, out_dir, 'diffDisLin', 'rts_diffDisLin_manu_cd', -60, 61, 10, [0, 110])

    # diffSloLin (difference between retreat distance along slope and manually drawn line)
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018_shp, c_RTS_info_2018vs2019_shp, out_dir, 'diffSloLin', 'rts_diffSloLin_manu_cd', -60, 61, 10, [0, 110])

    # diffCenLin (difference between retreat distance across centroid of old polygon based on medial circle and manually draw line)
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018_shp, c_RTS_info_2018vs2019_shp, out_dir, 'diffCenLin', 'rts_diffCenLin_manu_cd', -60, 61, 10, [0, 110])

    # diffCenLin (difference between retreat distance across centroid of old polygon based on medial circle and manually draw line)
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018_shp, c_RTS_info_2018vs2019_shp, out_dir, 'diffCenLin', 'rts_diffCenLin_manu_cd', -60, 61, 10, [0, 110])

    # ReDis_std (retreat distance variation)
    draw_two_hist_of_cd(c_RTS_info_2017vs2018_shp, c_RTS_info_2018vs2019_shp, out_dir, 'ReDis_std', 'rts_ReDis_std_manu_cd', 0, 71, 5, [0, 70])


def draw_hist_for_RTS_change_exp7():

    ##########################################################################################
    # # plot histogram on RTS change (group info from one or multiple change polygons) based on exp7 of thaw slumps in Beiluhe
    out_dir = os.path.expanduser('~/Data/Qinghai-Tibet/beiluhe/beiluhe_planet/polygon_based_ChangeDet/autoMap_exp7_2017To2019')
    shp_dir = os.path.expanduser('~/Data/Qinghai-Tibet/beiluhe/beiluhe_planet/polygon_based_ChangeDet/autoMap_exp7_2017To2019')
    c_RTS_info_2017vs2018_shp = os.path.join(shp_dir, 'rts_change_2017vs2018.shp')
    c_RTS_info_2018vs2019_shp = os.path.join(shp_dir, 'rts_change_2018vs2019.shp')

    # ## sum area
    # # draw_two_hist_of_cd(c_RTS_info_2017vs2018_shp,c_RTS_info_2018vs2019_shp,out_dir,'sum_c_area','rts_sum_area_manu_cd',0, 2.6, 0.2, [0, 145])
    #
    # ## max area (the maximum (in area) change polygon for an thaw slump)
    # # draw_two_hist_of_cd(c_RTS_info_2017vs2018_shp, c_RTS_info_2018vs2019_shp, out_dir, 'max_c_area', 'rts_max_area_manu_cd', 0, 2.6, 0.2, [0, 170])
    #
    # ## count of change polygons
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018_shp, c_RTS_info_2018vs2019_shp, out_dir, 'c_poly_num', 'rts_c_poly_num_manu_cd', 0, 20, 1, [0, 100])
    #
    # ## maximum retreat distance (based on medial circle)
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018_shp, c_RTS_info_2018vs2019_shp, out_dir, 'max_re_dis', 'rts_max_re_dis_manu_cd', 5, 81, 5, [0, 55])
    #
    # ## maxDisLin (retread distance from manual delineation)
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018_shp, c_RTS_info_2018vs2019_shp, out_dir, 'maxDisLin','rts_maxDisLin_manu_cd', 5, 81, 5, [0, 55])
    #
    # ## diffDisLin (difference between maximum retreat distance based on medial circle and manually drawn line)
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018_shp, c_RTS_info_2018vs2019_shp, out_dir, 'diffDisLin', 'rts_diffDisLin_manu_cd', -60, 61, 10, [0, 110])
    #
    # ## diffSloLin (difference between retreat distance along slope and manually drawn line)
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018_shp, c_RTS_info_2018vs2019_shp, out_dir, 'diffSloLin', 'rts_diffSloLin_manu_cd', -60, 61, 10, [0, 110])
    #
    # ## diffCenLin (difference between retreat distance across centroid of old polygon based on medial circle and manually draw line)
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018_shp, c_RTS_info_2018vs2019_shp, out_dir, 'diffCenLin', 'rts_diffCenLin_manu_cd', -60, 61, 10, [0, 110])
    #
    # ## diffCenLin (difference between retreat distance across centroid of old polygon based on medial circle and manually draw line)
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018_shp, c_RTS_info_2018vs2019_shp, out_dir, 'diffCenLin', 'rts_diffCenLin_manu_cd', -60, 61, 10, [0, 110])
    #
    # ## ReDis_std (retreat distance variation)
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018_shp, c_RTS_info_2018vs2019_shp, out_dir, 'ReDis_std', 'rts_ReDis_std_manu_cd', 0, 71, 5, [0, 70])


    pass

if __name__ == "__main__":

    #  plot histogram on RTS change (group info from one or multiple change polygons) based on manual delineation of thaw slumps in Beiluhe
    # draw_hist_for_RTS_change_manu()

    draw_hist_for_RTS_change_exp7()


    os.system('rm processLog.txt')
    # not used, since we move files in the previous steps
    # os.system('rm *.jpg')