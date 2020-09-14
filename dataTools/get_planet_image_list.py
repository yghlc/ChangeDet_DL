#!/usr/bin/env python
# Filename: get_planet_image_list 
"""
introduction: get images list of downloaded Planet image in time period and spatial extent

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 16 July, 2020
"""

import sys,os
from optparse import OptionParser

sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import basic_src.io_function as io_function
import basic_src.basic as basic
import vector_gpd

from datetime import datetime
import json
import time

# import thest two to make sure load GEOS dll before using shapely
import shapely
from shapely.geometry import mapping # transform to GeJSON format
from shapely.geometry import shape

from xml.dom import minidom


import pandas as pd

def read_cloud_cover(metadata_path):
    xmldoc = minidom.parse(metadata_path)
    nodes = xmldoc.getElementsByTagName("opt:cloudCoverPercentage")
    cloud_per = float(nodes[0].firstChild.data)
    # print(cloud_per)
    return cloud_per

def read_acquired_date(metadata_path):
    xmldoc = minidom.parse(metadata_path)
    nodes = xmldoc.getElementsByTagName("ps:acquisitionDateTime")
    #acquisitionDatetime = float(nodes[0].firstChild.data)
    # 2016-08-23T03:27:21+00:00
    # acquisitionDatetime = datetime.strptime(nodes[0].firstChild.data, '%y-%m-%dT%H:%M:%S')
    acquisitionDate = pd.to_datetime(nodes[0].firstChild.data).date()
    # acquisitionDateTime = pd.to_datetime(nodes[0].firstChild.data).to_pydatetime()
    # print(cloud_per)
    return acquisitionDate


def get_Planet_SR_image_list_overlap_a_polygon(polygon,geojson_list, cloud_cover_thr, save_list_path=None):
    '''
    get planet surface reference (SR) list overlap a polygon (within or overlap part of the polygon)
    :param polygon: polygon in the shapely format
    :param geojson_list:
    :param save_list_path: save the list to a txt file.
    :return:
    '''

    image_path_list = []
    cloud_cover_list = []
    for geojson_file in geojson_list:
        # print(geojson_file)
        with open(geojson_file) as json_obj:
            geom = json.load(json_obj)
        img_ext = shape(geom)

        inter = polygon.intersection(img_ext)
        if inter.is_empty is False:
            img_dir = os.path.splitext(geojson_file)[0]
            sr_img_paths = io_function.get_file_list_by_pattern(img_dir,'*_SR.tif')
            if len(sr_img_paths) < 0:
                basic.outputlogMessage('warning, no SR image in %s, try to find Analytic images'%img_dir)
                sr_img_paths = io_function.get_file_list_by_pattern(img_dir, '*AnalyticMS.tif')
                
            meta_data_paths = io_function.get_file_list_by_pattern(img_dir,'*_metadata.xml')
            if len(sr_img_paths) != len(meta_data_paths):
                # raise ValueError('the count of metadata files and images is different')
                basic.outputlogMessage('warning: the count of metadata files and images is different for %s'%img_dir)
                continue

            if len(sr_img_paths) < 1:
                basic.outputlogMessage('warning, no Planet SR image in the %s'%img_dir)
            elif len(sr_img_paths) > 1:
                basic.outputlogMessage('warning, more than one Planet SR image in the %s'%img_dir)
            else:
                # check cloud cover
                cloud_cover = read_cloud_cover(meta_data_paths[0])
                if cloud_cover > cloud_cover_thr:
                    continue

                # add image
                image_path_list.append(sr_img_paths[0])
                cloud_cover_list.append(cloud_cover)

    if save_list_path is not None:
        with open(save_list_path,'w') as f_obj:
            for image_path in image_path_list:
                f_obj.writelines(image_path + '\n')

    return image_path_list, cloud_cover_list

def read_a_meta_of_scene(scene_folder_or_geojson,scene_id_list):

    # get scene id
    if os.path.isfile(scene_folder_or_geojson): # geojson file
       scene_id = os.path.splitext(os.path.basename(scene_folder_or_geojson))[0]
       geojson_path = scene_folder_or_geojson
       scene_folder = os.path.splitext(scene_folder_or_geojson)[0]
    else:
        # scene_folder
        scene_id = os.path.basename(scene_folder_or_geojson)
        geojson_path = scene_folder_or_geojson + '.geojson'
        scene_folder = scene_folder_or_geojson

    # if already exists
    if scene_id in scene_id_list:
        return None,None,None,None,None,None,None,None,None

    print(scene_id)

    # get metadata path
    cloud_cover = 101
    acquisitionDate = datetime(1970,1,1)
    metadata_paths = io_function.get_file_list_by_pattern(scene_folder,'*metadata.xml')
    if len(metadata_paths) < 1:
        basic.outputlogMessage('warning, there is no metadata file in %s'%scene_folder)
    elif len(metadata_paths) > 1:
        basic.outputlogMessage('warning, there are more than one metadata files in %s' % scene_folder)
    else:
        # read metadata
        metadata_path = metadata_paths[0]
        cloud_cover = read_cloud_cover(metadata_path)
        acquisitionDate =  read_acquired_date(metadata_path)

    assets = io_function.get_file_list_by_pattern(scene_folder,'*')
    asset_count = len(assets)
    asset_files = sorted([ os.path.basename(item) for item in assets])
    asset_files =','.join(asset_files)

    image_type = 'analytic'  # 'analytic_sr' (surface reflectance) or 'analytic'
    sr_tif = io_function.get_file_list_by_pattern(scene_folder,'*_SR.tif')
    if len(sr_tif) == 1:
        image_type = 'analytic_sr'

    # consider as the downloading time
    if os.path.isfile(geojson_path):
        modified_time = io_function.get_file_modified_time(geojson_path)
    else:
        geojson_path = ''
        modified_time = io_function.get_file_modified_time(scene_folder)


    return scene_id,cloud_cover,acquisitionDate,geojson_path,scene_folder,asset_count,image_type,asset_files,modified_time



def save_planet_images_to_excel(image_dir,save_xlsx):

    if os.path.isfile(image_dir):
        basic.outputlogMessage('Input %s is a file, expected a folder'%image_dir)
        return False

    # read save_xlsx if it exist
    scene_id_list = []
    # may be not good to exclude these the scene id if we want to update some records.
    # if os.path.isfile(save_xlsx):
    #     df = pd.read_excel(save_xlsx)
    #     scene_id_list.extend(df['scene_id'].to_list())

    old_scene_count = len(scene_id_list)
    # print(old_scene_count)

    # get scene folders (idealy, the number of scene folder are the same to the one of geojson files)
    scene_geojson_folders = io_function.get_file_list_by_pattern(image_dir,'????????_??????_*')     # acquired date_time
    if len(scene_geojson_folders) < 1:
        raise ValueError('There is no scene folder or geojson in %s'%image_dir)


    # read each scene and save to xlsx

    cloud_cover_list = []
    acqui_date_list = []        # acquisitionDate
    geojson_file_list = []
    scene_folder_list = []
    asset_count_list = []
    asset_files_list = []
    image_type_list = []    # 'analytic_sr' (surface reflectance) or 'analytic'
    modife_time_list = []

    scene_without_asset = []       # find scene folders without asset

    for a_scene_file_dir in scene_geojson_folders:
        # print(id)
        scene_id, cloud_cover, acquisitionDate, geojson_path, scene_folder, asset_count, image_type,asset_files, modified_time = \
        read_a_meta_of_scene(a_scene_file_dir, scene_id_list)

        if scene_id is None:
            continue

        scene_id_list.append(scene_id)
        cloud_cover_list.append(cloud_cover)
        acqui_date_list.append(acquisitionDate)
        geojson_file_list.append(geojson_path)
        scene_folder_list.append(scene_folder)
        asset_count_list.append(asset_count)
        asset_files_list.append(asset_files)
        image_type_list.append(image_type)
        modife_time_list.append(modified_time)

        if asset_count == 0:
            scene_without_asset.append(a_scene_file_dir)


    add_scene_count = len(scene_id_list) - old_scene_count
    if add_scene_count < 1:
        basic.outputlogMessage('No new downloaded scenes in %s, skip writting xlsx'%image_dir)
        return True

    scene_table = {'scene_id': scene_id_list,
                   'cloud_cover': cloud_cover_list,
                   'acquisitionDate':acqui_date_list,
                   'downloadTime':modife_time_list,
                   'asset_count': asset_count_list,
                   'image_type': image_type_list,
                   'asset_files':asset_files_list,
                   'geojson':geojson_file_list,
                   'folder':scene_folder_list
                   }

    # # put then in order
    # import collections
    # dict_top1_per = collections.OrderedDict(sorted(dict_top1_per.items()))

    df = pd.DataFrame(scene_table) #.set_index('vertical_offset')
    with pd.ExcelWriter(save_xlsx) as writer:
        df.to_excel(writer)
        basic.outputlogMessage('write records of downloaded scenes to %s'%save_xlsx)

    scene_folder_no_assets_txt = os.path.splitext(save_xlsx) + 'scenes_noAsset_.txt'
    with open('scene_folder_no_assets_txt', 'w') as f_obj:
        for scene_dir in scene_without_asset:
            f_obj.writelines(scene_dir + '\n')

    return True



def main(options, args):

    image_dir = args[0]

    # get the file list in folder and save to excel
    if options.save_xlsx_path is not None:
        save_xlsx = options.save_xlsx_path
        save_planet_images_to_excel(image_dir,save_xlsx)
        return True

    shp_path = args[1]

    cloud_cover_thr = options.cloud_cover  # 0.3
    cloud_cover_thr =  cloud_cover_thr* 100     # in xml, it is percentage

    geojson_list = io_function.get_file_list_by_ext('.geojson',image_dir,bsub_folder=True)
    if len(geojson_list) < 1:
        raise ValueError('There is no geojson files in %s'%image_dir)

    # get files
    extent_polygons = vector_gpd.read_polygons_gpd(shp_path)
    for idx, polygon in enumerate(extent_polygons):
        save_list_txt = 'planet_sr_image_poly_%d.txt'%idx
        get_Planet_SR_image_list_overlap_a_polygon(polygon,geojson_list,cloud_cover_thr,save_list_path=save_list_txt)

        pass




    #TODO: filter the image using the acquired time


    pass

if __name__ == "__main__":

    usage = "usage: %prog [options] image_dir polygon_shp "
    parser = OptionParser(usage=usage, version="1.0 2020-07-16")
    parser.description = 'Introduction: get planet image list  '
    # parser.add_option("-s", "--start_date",default='2018-04-30',
    #                   action="store", dest="start_date",
    #                   help="start date for inquiry, with format year-month-day, e.g., 2018-05-23")
    # parser.add_option("-e", "--end_date",default='2018-06-30',
    #                   action="store", dest="end_date",
    #                   help="the end date for inquiry, with format year-month-day, e.g., 2018-05-23")
    parser.add_option("-c", "--cloud_cover",
                      action="store", dest="cloud_cover", type=float,default=0.3,
                      help="the could cover threshold, only accept images with cloud cover less than the threshold")
    # parser.add_option("-i", "--item_types",
    #                   action="store", dest="item_types",default='PSScene4Band',
    #                   help="the item types, e.g., PSScene4Band,PSOrthoTile")
    # parser.add_option("-a", "--planet_account",
    #                   action="store", dest="planet_account",default='huanglingcao@link.cuhk.edu.hk',
    #                   help="planet email account, e.g., huanglingcao@link.cuhk.edu.hk")
    parser.add_option("-x", "--save_xlsx_path",
                      action="store", dest="save_xlsx_path",
                      help="save the sence lists to xlsx file")



    (options, args) = parser.parse_args()
    if len(sys.argv) < 2 or len(args) < 1:
        parser.print_help()
        sys.exit(2)

    basic.setlogfile('get_planet_image_list_%s.log'%str(datetime.date(datetime.now())))

    main(options, args)

