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
import basic_src.basic as basic

import basic_src.io_function as io_function
import basic_src.map_projection as map_projection

import pandas as pd
import geopandas as gpd


import numpy as np

from plot_histogram import draw_one_list_histogram

# a structure (class) for information of developing RTSs
class change_RTS():
    def __init__(self,changePolygon_idx,row):
        # key = ""            # old_index + new_index. the key of dict object is the same to this.
        self.old_index = -1      # polygon index (0-based) in the old shape file
        self.new_index = -1      # polygon index (0-based) in the new shape file
        self.change_poly_index = []
        self.change_poly_count = -1

        self.max_change_area = -1
        self.min_change_area = -1
        self.avg_change_area = -1
        self.sum_change_area = -1
        self.change_area_list = []

        # for each change polygon, it already has max, min, avg, media retreat distance, choose max as the retreat distance,
        # then calculate the max, min, and avg values.
        self.max_retreat_dis = -1
        self.min_retreat_dis = -1
        self.avg_retreat_dis = -1
        self.retreat_dis_list = []

        # for each change polygon, it may (may not) have retreat distance at the direction maximum elevation difference
        self.max_retreat_dis_slope = -1
        self.min_retreat_dis_slope = -1
        self.avg_retreat_dis_slope = -1
        self.retreat_dis_slope_list = []

        # for each change polygon, it may (may not) have retreat distance at the direction across geometric center of
        # old polygon and one medial circle
        self.max_retreat_dis_centroid = -1
        self.min_retreat_dis_centroid = -1
        self.avg_retreat_dis_centroid = -1
        self.retreat_dis_centroid_list = []

        # for each change polygon, it may (may not) have retreat distance along the line (manually draw)
        self.max_retreat_dis_line = -1
        self.min_retreat_dis_line = -1
        self.avg_retreat_dis_line = -1
        self.retreat_dis_line_list = []

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

        if 'e_dis_slop' in row.keys():
            self.retreat_dis_slope_list.append(row['e_dis_slop'])

        if 'c_dis_cen' in row.keys():
            self.retreat_dis_centroid_list.append(row['c_dis_cen'])

        if 'e_dis_line' in row.keys():
            self.retreat_dis_line_list.append(row['e_dis_line'])

        self.__update_max_min_avg_values()

    def __update_max_min_avg_values(self):

        area_np_values = np.asarray(self.change_area_list, dtype=np.float64)
        self.max_change_area = np.max(area_np_values)
        self.min_change_area = np.min(area_np_values)
        self.avg_change_area = np.average(area_np_values)
        self.sum_change_area = np.sum(area_np_values)

        retreat_np_dis = np.asarray(self.retreat_dis_list, dtype=np.float64)
        self.max_retreat_dis = np.max(retreat_np_dis)
        self.min_retreat_dis = np.min(retreat_np_dis)
        self.avg_retreat_dis = np.average(retreat_np_dis)

        if len(self.retreat_dis_slope_list) > 0:
            retreat_np_dis_slope = np.asarray(self.retreat_dis_slope_list, dtype=np.float64)
            self.max_retreat_dis_slope = np.max(retreat_np_dis_slope)
            self.min_retreat_dis_slope = np.min(retreat_np_dis_slope)
            self.avg_retreat_dis_slope = np.average(retreat_np_dis_slope)

        if len(self.retreat_dis_centroid_list) > 0:
            retreat_np_dis_centroid = np.asarray(self.retreat_dis_centroid_list, dtype=np.float64)
            self.max_retreat_dis_centroid = np.max(retreat_np_dis_centroid)
            self.min_retreat_dis_centroid = np.min(retreat_np_dis_centroid)
            self.avg_retreat_dis_centroid = np.average(retreat_np_dis_centroid)

        if len(self.retreat_dis_line_list) > 0:
            retreat_np_dis_line = np.asarray(self.retreat_dis_line_list, dtype=np.float64)
            self.max_retreat_dis_line = np.max(retreat_np_dis_line)
            self.min_retreat_dis_line = np.min(retreat_np_dis_line)
            self.avg_retreat_dis_line = np.average(retreat_np_dis_line)

        self.change_poly_count = len(self.change_poly_index)

        pass

def read_attribute(change_RTS_info,field_name):
    values = []
    for key in change_RTS_info.keys():
        if field_name == 'max_area':
            values.append(change_RTS_info[key].max_change_area)
        elif field_name == 'min_area':
            values.append(change_RTS_info[key].min_change_area)
        elif field_name == 'average_area':
            values.append(change_RTS_info[key].avg_change_area)
        elif field_name == 'sum_area':
            values.append(change_RTS_info[key].sum_change_area)
        elif field_name == 'max_retreat_distance':
            values.append(change_RTS_info[key].max_retreat_dis)
        elif field_name == 'min_retreat_distance':
            values.append(change_RTS_info[key].min_retreat_dis)
        elif field_name == 'average_retreat_distance':
            values.append(change_RTS_info[key].avg_retreat_dis)
        elif field_name == 'change_polygon_count':
            values.append(change_RTS_info[key].change_poly_count)
        else:
            raise ValueError('field name: %s not found'%field_name)

    return values

def draw_one_value_hist(change_RTS_info,field_name, out_dir, output,logfile,bin_min,bin_max,bin_width,ylim):

    values = read_attribute(change_RTS_info, field_name)
    if 'area' in field_name:                      # m^2 to ha
        values = [item/10000.0 for item in values]

    xlabelrotation = None
    # if 'area' in field_name or 'retreat' in field_name:
    #     xlabelrotation = 90
    xlabelrotation = 90

    bins = np.arange(bin_min, bin_max, bin_width)

    # plot histogram of slope values
    # value_list,output,bins=None,labels=None,color=None,hatch=""
    draw_one_list_histogram(values, output,bins=bins,color=['grey'],xlabelrotation=xlabelrotation,ylim=ylim )  # ,hatch='-'
    io_function.move_file_to_dst('processLog.txt', os.path.join(out_dir, logfile), overwrite=True)
    io_function.move_file_to_dst(output, os.path.join(out_dir, output), overwrite=True)

def group_change_polygons(change_shp, old_shp=None, new_shp=None,save_path=None):
    '''
    group change polygons that belongs to the same thaw slumps
    :param change_shp:
    :param old_shp:
    :param new_shp:
    :param save_path: save the group information (multi-polygon) to shapefile
    :return:
    '''
    # check file existence
    io_function.is_file_exist(change_shp)
    if old_shp is not None: io_function.is_file_exist(old_shp)
    if new_shp is not None: io_function.is_file_exist(new_shp)

    # check old and new shape file name
    # get old shape file path and new file path
    old_file = set(vector_gpd.read_attribute_values_list(change_shp,'old_file')).pop()
    new_file = set(vector_gpd.read_attribute_values_list(change_shp,'new_file')).pop()

    if old_shp is not None and os.path.basename(old_shp) != old_file:
        raise ValueError('The old shape file (%s) is different from the one stored in the attributes of %s' % (old_shp, change_shp))
    if new_shp is not None and os.path.basename(new_shp) != new_file:
        raise ValueError('The new shape file (%s) is different from the one stored in the attributes of %s' % (new_shp, change_shp))

    # read the shape file
    c_shapefile = gpd.read_file(change_shp)
    # c_polygons = c_shapefile.geometry.values

    # old_shapefile = gpd.read_file(old_shp)
    # print('old_polygon count:', len(old_shapefile.geometry.values))
    # new_shapefile = gpd.read_file(new_shp)
    # print('new_polygon count:', len(new_shapefile.geometry.values))

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

    # save change polygons (multi-polygon) belonging to the same RTS to the same file
    if save_path is not None:

        c_polygons = c_shapefile.geometry.values

        old_index_list = []
        new_index_list =  []
        # self.change_poly_index = []
        change_poly_count_list = []

        max_change_area_list = []
        min_change_area_list = []
        avg_change_area_list = []
        sum_change_area_list = []
        # change_area_list = []

        # for each change polygon, it already has max, min, avg, media retreat distance, choose max as the retreat distance,
        # the retreat distance is calculated based on the max medial circle.
        # then calculate the max, min, and avg values.
        max_retreat_dis_list = []
        min_retreat_dis_list = []
        avg_retreat_dis_list = []
        # self.retreat_dis_list = []

        max_retreat_dis_slope_list = []
        min_retreat_dis_slope_list = []
        avg_retreat_dis_slope_list = []

        max_retreat_dis_centroid_list = []
        min_retreat_dis_centroid_list = []
        avg_retreat_dis_centroid_list = []

        # this one, is based on manually draw lines, can be consider as ground truths.
        max_retreat_dis_line_list = []
        min_retreat_dis_line_list = []
        avg_retreat_dis_line_list = []

        # calculate the variation (use standard deviation ) of three retreat distance (medial circle, along slope, across centroid)
        std_retreat_dis_list = []

        diff_retreat_dis_line_list = []            # calculate the difference between max_retreat_dis and max_retreat_dis_line (ground truth)
        diff_retreat_slope_line_list = []          # calculate the difference between retreat along slope and max_retreat_dis_line (ground truth)
        diff_retreat_centroid_line_list = []       # calculate the difference between retreat across centroid of old polygon and max_retreat_dis_line (ground truth)

        multi_polygon_list = []

        new_shp_name_list = []
        old_shp_name_list = []

        for key in change_RTS_pair.keys():
            # print(key, change_RTS_pair[key].max_retreat_dis,change_RTS_pair[key].max_change_area)
            new_shp_name_list.append(new_file)
            old_shp_name_list.append(old_file)

            old_index_list.append(change_RTS_pair[key].old_index)
            new_index_list.append(change_RTS_pair[key].new_index)
            change_poly_count_list.append(change_RTS_pair[key].change_poly_count)
            max_change_area_list.append(change_RTS_pair[key].max_change_area)
            min_change_area_list.append(change_RTS_pair[key].min_change_area)
            avg_change_area_list.append(change_RTS_pair[key].avg_change_area)
            sum_change_area_list.append(change_RTS_pair[key].sum_change_area)

            max_retreat_dis_list.append(change_RTS_pair[key].max_retreat_dis)
            min_retreat_dis_list.append(change_RTS_pair[key].min_retreat_dis)
            avg_retreat_dis_list.append(change_RTS_pair[key].avg_retreat_dis)

            max_retreat_dis_slope_list.append(change_RTS_pair[key].max_retreat_dis_slope)
            min_retreat_dis_slope_list.append(change_RTS_pair[key].min_retreat_dis_slope)
            avg_retreat_dis_slope_list.append(change_RTS_pair[key].avg_retreat_dis_slope)

            max_retreat_dis_centroid_list.append(change_RTS_pair[key].max_retreat_dis_centroid)
            min_retreat_dis_centroid_list.append(change_RTS_pair[key].min_retreat_dis_centroid)
            avg_retreat_dis_centroid_list.append(change_RTS_pair[key].avg_retreat_dis_centroid)

            # calculate the variation (use standard deviation ) of three retreat distance (medial circle, along slope, across centroid)
            multi_re_dis = np.array([change_RTS_pair[key].max_retreat_dis, change_RTS_pair[key].max_retreat_dis_slope,change_RTS_pair[key].max_retreat_dis_centroid ])
            std_retreat_dis_list.append(np.std(multi_re_dis))

            # calculate the difference between automatic calculated distance and manually drawn ones
            if change_RTS_pair[key].max_retreat_dis_line > 0:
                # if max_retreat_dis_line is valid
                diff_retreat_dis_line_list.append(change_RTS_pair[key].max_retreat_dis - change_RTS_pair[key].max_retreat_dis_line)
                diff_retreat_slope_line_list.append(change_RTS_pair[key].max_retreat_dis_slope - change_RTS_pair[key].max_retreat_dis_line)
                diff_retreat_centroid_line_list.append(change_RTS_pair[key].max_retreat_dis_centroid - change_RTS_pair[key].max_retreat_dis_line)
            else:
                diff_retreat_dis_line_list.append(0)
                diff_retreat_slope_line_list.append(0)
                diff_retreat_centroid_line_list.append(0)

            # diff_max_retreat_dis_slope_list.append(change_RTS_pair[key].max_retreat_dis_slope - change_RTS_pair[key].max_retreat_dis)
            # diff_max_retreat_dis_centroid_list.append(change_RTS_pair[key].max_retreat_dis_centroid - change_RTS_pair[key].max_retreat_dis)

            # only the max_retreat_dis_line can be trust, because usually, we only have one line for each RTS
            # other parts of expanding area don't have line, then the retreat value will be set as 0.
            max_retreat_dis_line_list.append(change_RTS_pair[key].max_retreat_dis_line)
            min_retreat_dis_line_list.append(change_RTS_pair[key].min_retreat_dis_line)
            avg_retreat_dis_line_list.append(change_RTS_pair[key].avg_retreat_dis_line)

            rts_c_polygons = [c_polygons[item] for item in change_RTS_pair[key].change_poly_index]
            multi_polygon_list.append(vector_gpd.polygons_to_a_MultiPolygon(rts_c_polygons))

        # save the polygon changes
        changePolygons_df = pd.DataFrame({'old_file': old_shp_name_list,
                                     'new_file': new_shp_name_list,
                                     'old_index': old_index_list,
                                     'new_index': new_index_list,
                                     'c_poly_num': change_poly_count_list,
                                     'max_c_area': max_change_area_list,
                                     'min_c_area': min_change_area_list,
                                     'avg_c_area': avg_change_area_list,
                                     'sum_c_area': sum_change_area_list,
                                     'max_re_dis': max_retreat_dis_list,
                                     'min_re_dis': min_retreat_dis_list,
                                     'avg_re_dis': avg_retreat_dis_list,
                                     'diffDisLin': diff_retreat_dis_line_list,
                                     'maxDisSlo': max_retreat_dis_slope_list,
                                     'minDisSlo': min_retreat_dis_slope_list,
                                     'avgDisSlo': avg_retreat_dis_slope_list,
                                     'diffSloLin': diff_retreat_slope_line_list,
                                     'maxDisCen': max_retreat_dis_centroid_list,
                                     'minDisCen': min_retreat_dis_centroid_list,
                                     'avgDisCen': avg_retreat_dis_centroid_list,
                                     'diffCenLin': diff_retreat_centroid_line_list,
                                     'maxDisLin': max_retreat_dis_line_list,            # only the max_retreat_dis_line can be trust
                                     'minDisLin': min_retreat_dis_line_list,
                                     'avgDisLin': avg_retreat_dis_line_list,
                                     'ReDis_std': std_retreat_dis_list,
                                     'ChangePolygons': multi_polygon_list
                                     })

        wkt_string = map_projection.get_raster_or_vector_srs_info_wkt(change_shp)
        vector_gpd.save_polygons_to_files(changePolygons_df, 'ChangePolygons', wkt_string, save_path)

        # save to excel format
        excel_save_path = os.path.splitext(save_path)[0] + '.xlsx'
        print(excel_save_path)
        # output top 1 to excel
        with pd.ExcelWriter(excel_save_path) as writer:
            del changePolygons_df['ChangePolygons']
            changePolygons_df.to_excel(writer, sheet_name=os.path.splitext(os.path.basename(excel_save_path))[0])

    # for key in change_RTS_pair.keys():
    #     print(key, change_RTS_pair[key].max_retreat_dis,change_RTS_pair[key].max_change_area)

    return change_RTS_pair


def draw_two_hist_of_cd(change_RTS_info_0vs1,change_RTS_info_1vs2, out_dir, field_name,out_pre_name, bin_min,bin_max,bin_width,ylim):

    draw_one_value_hist(change_RTS_info_0vs1,field_name,out_dir,out_pre_name+'_2017vs2018.jpg',out_pre_name+'_2017vs2018.txt',bin_min,bin_max,bin_width,ylim)
    draw_one_value_hist(change_RTS_info_1vs2,field_name,out_dir, out_pre_name+'_2018vs2019.jpg',out_pre_name+'_2018vs2019.txt',bin_min,bin_max,bin_width,ylim)


def statistic_using_manu_results():

    ##########################################################################################
    # # conduct statistic of change RTSs on the ground truth
    # out_dir = os.path.expanduser('~/Data/Qinghai-Tibet/beiluhe/result/result_multi_temporal_changes_17-19July/BLH_2017To2019_manual_delineation')
    shp_dir = os.path.expanduser('~/Data/Qinghai-Tibet/beiluhe/thaw_slumps')
    ground_truth_201707 = os.path.join(shp_dir, 'train_polygons_for_planet_201707/blh_manu_RTS_utm_201707.shp')
    ground_truth_201807 = os.path.join(shp_dir, 'train_polygons_for_planet_201807/blh_manu_RTS_utm_201807.shp')
    ground_truth_201907 = os.path.join(shp_dir, 'train_polygons_for_planet_201907/blh_manu_RTS_utm_201907.shp')

    #
    # # plot histogram on the change polygons (based on manual delineation) of thaw slumps in Beiluhe
    out_dir=os.path.expanduser('~/Data/Qinghai-Tibet/beiluhe/beiluhe_planet/polygon_based_ChangeDet/manu_blh_2017To2019_v2')
    shp_dir = os.path.expanduser('~/Data/Qinghai-Tibet/beiluhe/beiluhe_planet/polygon_based_ChangeDet/manu_blh_2017To2019_v2')
    manu_cd_2017vs2018 = os.path.join(shp_dir, 'change_manu_blh_2017To2019_v2_T_201707_vs_201807.shp')
    manu_cd_2018vs2019 = os.path.join(shp_dir, 'change_manu_blh_2017To2019_v2_T_201807_vs_201907.shp')

    c_RTS_info_2017vs2018 = group_change_polygons(manu_cd_2017vs2018,ground_truth_201707,ground_truth_201807,
                                                  save_path=os.path.join(out_dir,'rts_change_2017vs2018_v2.shp'))
    c_RTS_info_2018vs2019 = group_change_polygons(manu_cd_2018vs2019,ground_truth_201807,ground_truth_201907,
                                                  save_path=os.path.join(out_dir,'rts_change_2018vs2019_v2.shp'))


    ############################################################################################################
    ############drawing figure have been move to plot_histogram_rts_change.py ############

    # plot histogram of RTS change polygons, for each polygons
    # draw_one_value_hist(change_RTS_info, 'max_area', 'max_RTSmax_area_manu_2017vs2018.jpg', 'bins_RTSmax_area_manu_2017vs2018.txt', 0, 2.2, 0.1, [0, 120])

    # # # max area
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018, c_RTS_info_2018vs2019, out_dir,'max_area', 'RTS_max_area_manu', 0, 2.2, 0.1, [0, 120])
    # # # min area
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018, c_RTS_info_2018vs2019, out_dir, 'min_area', 'RTS_min_area_manu', 0, 2.2, 0.1, [0, 180])
    # # # average area
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018, c_RTS_info_2018vs2019, out_dir,'average_area', 'RTS_avg_area_manu', 0, 2.2, 0.1, [0, 150])
    # # sum area
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018, c_RTS_info_2018vs2019, out_dir,'sum_area', 'RTS_sum_area_manu', 0, 2.2, 0.1, [0, 150])

    # max_retreat_distance
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018, c_RTS_info_2018vs2019, 'max_retreat_distance', 'RTS_max_retreat_dis_manu', 0, 100, 5, [0, 60])

    # min_retreat_distance
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018, c_RTS_info_2018vs2019, 'min_retreat_distance', 'RTS_min_retreat_dis_manu', 0, 100, 5, [0, 110])

    # average_retreat_distance
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018, c_RTS_info_2018vs2019, 'average_retreat_distance', 'RTS_avg_retreat_dis_manu', 0, 100, 5, [0, 70])

    # change_polygon_count
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018, c_RTS_info_2018vs2019, 'change_polygon_count', 'RTS_change_polygon_count_manu', 1, 21, 1, [0, 110])


def statistic_using_auto_exp3_results():

    ##########################################################################################
    # plot histogram on the change polygons (based on exp3) of thaw slumps in Beiluhe
    out_dir = os.path.expanduser('~/Data/Qinghai-Tibet/beiluhe/beiluhe_planet/polygon_based_ChangeDet/autoMap_exp3_2017To2019')
    shp_dir = os.path.expanduser('~/Data/Qinghai-Tibet/beiluhe/beiluhe_planet/polygon_based_ChangeDet/autoMap_exp3_2017To2019')
    autoMap_exp3_cd_2017vs2018 = os.path.join(shp_dir, 'change_autoMap_exp3_2017To2019_T_I0_vs_I1.shp')
    autoMap_exp3_cd_2018vs2019 = os.path.join(shp_dir, 'change_autoMap_exp3_2017To2019_T_I1_vs_I2.shp')

    c_RTS_info_2017vs2018 = group_change_polygons(autoMap_exp3_cd_2017vs2018 )
    c_RTS_info_2018vs2019 = group_change_polygons(autoMap_exp3_cd_2018vs2019 )


def statistic_using_auto_exp5_results():
    ##########################################################################################
    # plot histogram on the change polygons (based on exp5) of thaw slumps in Beiluhe
    out_dir = os.path.expanduser('~/Data/Qinghai-Tibet/beiluhe/beiluhe_planet/polygon_based_ChangeDet/autoMap_exp5_2017To2019')
    shp_dir = os.path.expanduser('~/Data/Qinghai-Tibet/beiluhe/beiluhe_planet/polygon_based_ChangeDet/autoMap_exp5_2017To2019')
    autoMap_exp5_cd_2017vs2018 = os.path.join(shp_dir, 'change_autoMap_exp5_2017To2019_T_I0_vs_I1.shp')
    autoMap_exp5_cd_2018vs2019 = os.path.join(shp_dir, 'change_autoMap_exp5_2017To2019_T_I1_vs_I2.shp')

    c_RTS_info_2017vs2018 = group_change_polygons(autoMap_exp5_cd_2017vs2018,save_path=os.path.join(out_dir,'rts_change_2017vs2018.shp'))
    c_RTS_info_2018vs2019 = group_change_polygons(autoMap_exp5_cd_2018vs2019,save_path=os.path.join(out_dir,'rts_change_2018vs2019.shp'))

    # max area (exp3 has many false positive, so the total count of changing RTS is over 400)
    # draw_two_hist_of_cd(c_RTS_info_2017vs2018, c_RTS_info_2018vs2019, 'max_area', 'RTS_max_area_manu', 0, 2.2, 0.1, [0, 120])

def statistic_using_auto_exp7_results():

    ##########################################################################################
    # plot histogram on the change polygons (based on exp7) of thaw slumps in Beiluhe
    out_dir = os.path.expanduser('~/Data/Qinghai-Tibet/beiluhe/beiluhe_planet/polygon_based_ChangeDet/autoMap_exp7_2017To2019')
    shp_dir = os.path.expanduser('~/Data/Qinghai-Tibet/beiluhe/beiluhe_planet/polygon_based_ChangeDet/autoMap_exp7_2017To2019')
    autoMap_exp7_cd_2017vs2018 = os.path.join(shp_dir, 'change_autoMap_exp7_2017To2019_T_I0_vs_I1.shp')
    autoMap_exp7_cd_2018vs2019 = os.path.join(shp_dir, 'change_autoMap_exp7_2017To2019_T_I1_vs_I2.shp')

    c_RTS_info_2017vs2018 = group_change_polygons(autoMap_exp7_cd_2017vs2018,save_path=os.path.join(out_dir,'rts_change_2017vs2018.shp'))
    c_RTS_info_2018vs2019 = group_change_polygons(autoMap_exp7_cd_2018vs2019,save_path=os.path.join(out_dir,'rts_change_2018vs2019.shp'))


if __name__ == "__main__":


    statistic_using_manu_results()

    # statistic_using_auto_exp3_results()

    # statistic_using_auto_exp5_results()

    # statistic_using_auto_exp7_results()



    pass

