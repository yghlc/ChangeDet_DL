#!/usr/bin/env python
# Filename: statistic_change_RTSs 
"""
introduction: Conduct the statistic of how many thaw slumps have changes, and what is the retreat rates.

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 09 March, 2020
"""

import os, sys
# path of DeeplabforRS
deeplabforRS =  os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS')
sys.path.insert(0, deeplabforRS)

import vector_gpd

import basic_src.io_function as io_function

import pandas as pd
import geopandas as gpd

import numpy as np


# a structure (class) for information of developing RTSs
class change_RTS():
    def __init__(self,changePolygon_idx,row):
        # key = ""            # old_index + new_index. the key of dict object is the same to this.
        self.old_index = -1      # polygon index (0-based) in the old shape file
        self.new_index = -1      # polygon index (0-based) in the new shape file
        self.change_poly_index = []
        self.max_change_area = -1
        self.min_change_area = -1
        self.avg_change_area = -1
        self.change_area_list = []

        # for each change polygon, it already has max, min, avg, media retreat distance, choose max as the retreat distance,
        # then calculate the max, min, and avg values.
        self.max_retreat_dis = -1
        self.min_retreat_dis = -1
        self.avg_retreat_dis = -1
        self.retreat_dis_list = []

        self.add_changeRTS_info(changePolygon_idx,row)

    def add_changeRTS_info(self,changePolygon_idx,row):

        if self.old_index == -1:
            self.old_index = row['old_index']
        elif self.old_index != row['old_index']:
            raise ValueError('has a different old_index')

        if self.new_index == -1:
            self.new_index = row['new_index']
        elif self.new_index != row['new_index']:
            raise ValueError('has a different new_index')

        self.change_poly_index.append(changePolygon_idx)
        self.change_area_list.append(row['INarea'])
        self.retreat_dis_list.append(row['e_max_dis'])      # choose the max retreat distance of this change polygon

        self.__update_max_min_avg_values()

    def __update_max_min_avg_values(self):

        area_np_values = np.asarray(self.change_area_list, dtype=np.float64)
        self.max_change_area = np.max(area_np_values)
        self.min_change_area = np.min(area_np_values)
        self.avg_change_area = np.average(area_np_values)

        retreat_np_dis = np.asarray(self.retreat_dis_list, dtype=np.float64)
        self.max_retreat_dis = np.max(retreat_np_dis)
        self.min_retreat_dis = np.min(retreat_np_dis)
        self.avg_retreat_dis = np.average(retreat_np_dis)

        pass



def group_change_polygons(change_shp, old_shp, new_shp, save_path):
    '''
    group change polygons that belongs to the same thaw slumps
    :param change_shp:
    :param old_shp:
    :param new_shp:
    :param save_path: save the group information to shapefile
    :return:
    '''
    # check file existence
    io_function.is_file_exist(change_shp)
    io_function.is_file_exist(old_shp)
    io_function.is_file_exist(new_shp)

    # check old and new shape file name
    # get old shape file path and new file path
    old_file = set(vector_gpd.read_attribute_values_list(change_shp,'old_file')).pop()
    new_file = set(vector_gpd.read_attribute_values_list(change_shp,'new_file')).pop()

    if os.path.basename(old_shp) != old_file:
        raise ValueError('The old shape file (%s) is different from the one stored in the attributes of %s' % (old_shp, change_shp))
    if os.path.basename(new_shp) != new_file:
        raise ValueError('The new shape file (%s) is different from the one stored in the attributes of %s' % (new_shp, change_shp))

    # read the shape file
    c_shapefile = gpd.read_file(change_shp)
    # c_polygons = c_shapefile.geometry.values

    old_shapefile = gpd.read_file(old_shp)
    print('old_polygon count:', len(old_shapefile.geometry.values))
    new_shapefile = gpd.read_file(new_shp)
    print('new_polygon count:', len(new_shapefile.geometry.values))

    change_RTS_pair = {}

    # go through each change polygon
    for idx, row in c_shapefile.iterrows():

        rts_pair_key = str(row['old_index'])+'_'+str(row['new_index'])
        if rts_pair_key in change_RTS_pair.keys():
            change_RTS_pair[rts_pair_key].add_changeRTS_info(idx, row)
        else:
            change_rts_obj = change_RTS(idx,row)
            change_RTS_pair[rts_pair_key] = change_rts_obj

        pass


    test =  1

    pass



if __name__ == "__main__":

    ##########################################################################################
    # # conduct statistic of change RTSs on the ground truth
    # out_dir = os.path.expanduser('~/Data/Qinghai-Tibet/beiluhe/result/result_multi_temporal_changes_17-19July/BLH_2017To2019_manual_delineation')
    shp_dir = os.path.expanduser('~/Data/Qinghai-Tibet/beiluhe/thaw_slumps')
    ground_truth_201707 = os.path.join(shp_dir, 'train_polygons_for_planet_201707/blh_manu_RTS_utm_201707.shp')
    ground_truth_201807 = os.path.join(shp_dir, 'train_polygons_for_planet_201807/blh_manu_RTS_utm_201807.shp')
    # ground_truth_201907 = os.path.join(shp_dir, 'train_polygons_for_planet_201907/blh_manu_RTS_utm_201907.shp')

    #
    # # plot histogram on the change polygons (based on manual delineation) of thaw slumps in Beiluhe
    out_dir=os.path.expanduser('~/Data/Qinghai-Tibet/beiluhe/beiluhe_planet/polygon_based_ChangeDet/manu_blh_2017To2019')
    shp_dir = os.path.expanduser('~/Data/Qinghai-Tibet/beiluhe/beiluhe_planet/polygon_based_ChangeDet/manu_blh_2017To2019')
    manu_cd_2017vs2018 = os.path.join(shp_dir, 'change_manu_blh_2017To2019_T_201707_vs_201807.shp')
    manu_cd_2018vs2019 = os.path.join(shp_dir, 'change_manu_blh_2017To2019_T_201807_vs_201907.shp')

    group_change_polygons(manu_cd_2017vs2018,ground_truth_201707,ground_truth_201807,'save_2017_2018_group.shp')

    pass

