#!/usr/bin/env python
# Filename: ArcticDEM_proc 
"""
introduction: prepare Arctic, unzip, crop, registration, and co-registration

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 26 December, 2020
"""


import os,sys
from optparse import OptionParser

deeplabforRS =  os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS')
sys.path.insert(0, deeplabforRS)
import vector_gpd
import basic_src.map_projection as map_projection
import basic_src.io_function as io_function
import basic_src.basic as basic

import basic_src.RSImageProcess as RSImageProcess
import basic_src.RSImage as RSImage
import basic_src.timeTools as timeTools

import operator

import re
re_stripID='[0-9]{8}_[0-9A-F]{16}_[0-9A-F]{16}'

def get_dem_path_in_unpack_tarball(out_dir):
    file_end = ['_dem.tif','_reg_dem.tif']   # Arctic strip and tile (mosaic) version
    for end in file_end:
        dem_tif = os.path.join(out_dir, os.path.basename(out_dir) + end)
        if os.path.isfile(dem_tif):
            return dem_tif
    return False

def process_dem_tarball(tar_list, work_dir,inter_format, extent_shp=None):
    '''
    process dem tarball one by one
    :param tar_list: tarball list
    :param work_dir: working dir, saving the unpacked results
    :param inter_format: format for saving files
    :param extent_shp: a shape file to crop tif, if None, then skip
    :return: a list of final tif files
    '''

    dem_tif_list = []
    tar_folder_list = []
    for targz in tar_list:
        # file existence check
        tar_base = os.path.basename(targz)[:-7]
        # files = io_function.get_file_list_by_pattern(tif_save_dir, tar_base + '*')
        # if len(files) == 1:
        #     basic.outputlogMessage('%s exist, skip processing tarball %s' % (files[0], targz))
        #     dem_tif_list.append(files[0])
        #     continue

        # unpack, it can check whether it has been unpacked
        out_dir = io_function.unpack_tar_gz_file(targz, work_dir)
        if out_dir is not False:
            dem_tif = get_dem_path_in_unpack_tarball(out_dir)
            if os.path.isfile(dem_tif):
                #TODO: registration for each DEM using dx, dy, dz in *reg.txt file
                reg_tif = dem_tif

                # crop
                if extent_shp is None:
                    crop_tif = reg_tif
                else:
                    # because later, we move the file to another foldeer, so we should not use 'VRT' format
                    crop_tif = RSImageProcess.subset_image_by_shapefile(reg_tif, extent_shp, format=inter_format)
                    if crop_tif is False:
                        basic.outputlogMessage('warning, crop %s faild' % reg_tif)
                        continue
                # # move to a new folder
                # new_crop_tif = os.path.join(tif_save_dir, os.path.basename(crop_tif))
                # io_function.move_file_to_dst(crop_tif, new_crop_tif)
                # dem_tif_list.append(new_crop_tif)
                dem_tif_list.append(crop_tif)
            else:
                basic.outputlogMessage('warning, no *_dem.tif in %s' % out_dir)

            tar_folder_list.append(out_dir)
        else:
            basic.outputlogMessage('warning, unpack %s faild' % targz)

        # break

    return dem_tif_list, tar_folder_list

def group_demTif_yearmonthDay(demTif_list, diff_days=30):
    '''
    groups DEM tif if the acquisition of their raw images is close (less than 30 days or others)
    :param demTif_list:
    :return:
    '''
    dem_groups = {}
    for tif in demTif_list:
        yeardate =  timeTools.get_yeardate_yyyymmdd(os.path.basename(tif))

        b_assgined = False
        for time in dem_groups.keys():
            if timeTools.diff_yeardate(time,yeardate) <= diff_days:
                dem_groups[time].append(tif)
                b_assgined = True
                break
        if b_assgined is False:
            dem_groups[yeardate] = [tif]

    return dem_groups


def group_demTif_strip_pair_ID(demTif_list):
    '''
    group dem tif based on the same pair ID, such as 20170226_1030010066648800_1030010066CDE700 (did not include satellite name)
    :param demTif_list:
    :return:
    '''

    dem_groups = {}
    for tif in demTif_list:
        strip_ids = re.findall(re_stripID, os.path.basename(tif))
        if len(strip_ids) != 1:
            print(strip_ids)
            raise ValueError('found zero or multiple strip IDs in %s, expect one'%tif)
        strip_id = strip_ids[0]
        if strip_id in dem_groups.keys():
            dem_groups[strip_id].append(tif)
        else:
            dem_groups[strip_id] = [tif]

    return dem_groups

def mosaic_dem_same_stripID(demTif_groups,save_tif_dir, resample_method, save_source=False, o_format='GTiff'):
    mosaic_list = []
    for key in demTif_groups.keys():
        save_mosaic = os.path.join(save_tif_dir, key+'.tif')
        # check file existence
        # if os.path.isfile(save_mosaic):
        b_save_mosaic = io_function.is_file_exist_subfolder(save_tif_dir,key+'.tif')
        if b_save_mosaic is not False:
            basic.outputlogMessage('warning, mosaic file: %s exist, skip'%b_save_mosaic)
            mosaic_list.append(b_save_mosaic)
            continue
        # save the source file for producing the mosaic
        if save_source:
            save_mosaic_source_txt = os.path.join(save_tif_dir, key + '_src.txt')
            io_function.save_list_to_txt(save_mosaic_source_txt,demTif_groups[key])

        # if len(demTif_groups[key]) == 1:
        #     io_function.copy_file_to_dst(demTif_groups[key][0],save_mosaic)
        # else:
        #     # RSImageProcess.mosaics_images(dem_groups[key],save_mosaic)
        #     RSImageProcess.mosaic_crop_images_gdalwarp(demTif_groups[key],save_mosaic,resampling_method=resample_method,o_format=o_format)

        # create mosaic, can handle only input one file
        RSImageProcess.mosaic_crop_images_gdalwarp(demTif_groups[key], save_mosaic, resampling_method=resample_method,o_format=o_format)
        mosaic_list.append(save_mosaic)

    return mosaic_list

def mosaic_dem_date(demTif_date_groups,save_tif_dir, resample_method,save_source=False,o_format='GTiff'):

    # convert the key in demTif_date_groups to string
    date_groups = {}
    for key in demTif_date_groups.keys():
        new_key = key.strftime('%Y%m%d') + '_dem'
        date_groups[new_key] = demTif_date_groups[key]

    # becuase the tifs have been grouped, so we can use mosaic_dem_same_stripID
    return mosaic_dem_same_stripID(date_groups,save_tif_dir,resample_method,save_source=save_source,o_format=o_format)

def check_dem_valid_per(dem_tif_list, work_dir, move_dem_threshold = None):
    '''
    get the valid pixel percentage for each DEM
    :param dem_tif_list:
    :param work_dir:
    :param move_dem_threshold: move a DEM to a sub-folder if its valid percentage small then the threshold
    :return:
    '''

    keep_dem_list = []

    dem_tif_valid_per = {}
    for tif in dem_tif_list:
        # RSImage.get_valid_pixel_count(tif)
        per = RSImage.get_valid_pixel_percentage(tif)
        dem_tif_valid_per[tif] = per
        keep_dem_list.append(tif)
    # sort
    dem_tif_valid_per_d = dict(sorted(dem_tif_valid_per.items(), key=operator.itemgetter(1), reverse=True))
    percent_txt = os.path.join(work_dir,'dem_valid_percent.txt')
    with open(percent_txt,'w') as f_obj:
        for key in dem_tif_valid_per_d:
            f_obj.writelines('%s %.4f\n'%(os.path.basename(key),dem_tif_valid_per_d[key]))
        basic.outputlogMessage('save dem valid pixel percentage to %s'%percent_txt)

    # only keep dem with valid pixel greater than a threshold
    if move_dem_threshold is not None:  # int or float
        keep_dem_list = []      # reset the list
        mosaic_dir_rm = os.path.join(work_dir,'dem_valid_lt_%.2f'%move_dem_threshold)
        io_function.mkdir(mosaic_dir_rm)
        for tif in dem_tif_valid_per.keys():
            if dem_tif_valid_per[tif] < move_dem_threshold:
                io_function.movefiletodir(tif,mosaic_dir_rm)
            else:
                keep_dem_list.append(tif)

    return keep_dem_list

def coregistration_dem():
    pass

def process_arcticDEM_tiles(tar_list,save_dir,inter_format, resample_method, extent_shp=None, b_rm_inter=True):
    '''
    process the mosaic (not multi-temporal) version of ArcticDEM
    :param tar_list:
    :param save_dir:
    :param inter_format:
    :param extent_shp:
    :param b_rm_inter:
    :return:
    '''

    # unpackage and crop to extent
    dem_tif_list, tar_folders = process_dem_tarball(tar_list, save_dir, inter_format, extent_shp=extent_shp)
    if len(dem_tif_list) < 1:
        raise ValueError('No DEM extracted from tarballs')

    # create mosaic for a relative small area with a extent
    if extent_shp is not None:
        dem_name = os.path.basename(tar_folders[0])[-7:]
        region_base = os.path.splitext(os.path.basename(extent_shp))[0]
        save_path = os.path.join(save_dir,region_base + '_' + dem_name + '_ArcticTileDEM.tif')

        RSImageProcess.mosaic_crop_images_gdalwarp(dem_tif_list, save_path, resampling_method=resample_method,o_format=inter_format)
        pass

    # remove intermediate files
    if b_rm_inter:
        basic.outputlogMessage('remove intermediate files')
        for folder in tar_folders:
            io_function.delete_file_or_dir(folder)

    return True

def is_ArcticDEM_tiles(tar_list):
    '''
    check whether it is mosaic version (tiles) of DEM
    :param tar_list:
    :return:
    '''
    tile_pattern = '^\d{2}_\d{2}_'
    for tar in tar_list:
        tar_base = os.path.basename(tar)
        tiles = re.findall(tile_pattern,tar_base)
        if len(tiles) == 1:
            pass
        else:
            basic.outputlogMessage('%s is not a tile of ArcticDEM'%tar)
            return False

    return True

def main(options, args):

    extent_shp = args[0]
    # ext_shp_prj = map_projection.get_raster_or_vector_srs_info_epsg(extent_shp)
    # reproject if necessary, it seems that the gdalwarp can handle different projection
    # if ext_shp_prj != 'EPSG:3413':  # EPSG:3413 is the projection ArcticDEM used
    #     extent_shp_reprj = io_function.get_name_by_adding_tail(extent_shp,'3413')
    #     vector_gpd.reproject_shapefile(extent_shp,'EPSG:3413',extent_shp_reprj)
    #     extent_shp = extent_shp_reprj

    tar_dir = options.ArcticDEM_dir
    save_dir = options.save_dir
    b_mosaic_id = options.create_mosaic_id
    b_mosaic_date = options.create_mosaic_date
    b_rm_inter = options.remove_inter_data
    keep_dem_percent = options.keep_dem_percent
    inter_format = options.format

    # get tarball list
    tar_list = io_function.get_file_list_by_ext('.gz',tar_dir,bsub_folder=False)
    if len(tar_list) < 1:
        raise ValueError('No input tar.gz files in %s'%tar_dir)

    if is_ArcticDEM_tiles(tar_list):
        basic.outputlogMessage('Input is the mosaic version of ArcticDEM')
        return process_arcticDEM_tiles(tar_list,save_dir,inter_format,'average',extent_shp=extent_shp,b_rm_inter=True)


    dem_tif_list,tar_folders = process_dem_tarball(tar_list,save_dir,inter_format,extent_shp=extent_shp)

    # groups DEM
    dem_groups = group_demTif_strip_pair_ID(dem_tif_list)

    # create mosaic (dem with the same strip pair ID)
    mosaic_dir = os.path.join(save_dir,'dem_stripID_mosaic')
    if b_mosaic_id:
        io_function.mkdir(mosaic_dir)
        mosaic_list = mosaic_dem_same_stripID(dem_groups,mosaic_dir,'average',o_format=inter_format)
        dem_tif_list = mosaic_list

        # get valid pixel percentage
        dem_tif_list = check_dem_valid_per(dem_tif_list,mosaic_dir,move_dem_threshold = keep_dem_percent)

    # groups DEM with original images acquired at the same year months
    dem_groups_date = group_demTif_yearmonthDay(dem_tif_list,diff_days=31)
    # sort based on yeardate in accending order : operator.itemgetter(0)
    dem_groups_date = dict(sorted(dem_groups_date.items(), key=operator.itemgetter(0)))
    # save to txt (json format)
    year_date_txt = os.path.join(mosaic_dir, 'year_date_tif.txt')
    io_function.save_dict_to_txt_json(year_date_txt,dem_groups_date)

    # merge DEM with close acquisition date
    mosaic_yeardate_dir = os.path.join(save_dir,'dem_date_mosaic')
    if b_mosaic_date:
        io_function.mkdir(mosaic_yeardate_dir)
        # this is the last output of mosaic, save to 'GTiff' format.
        mosaic_list = mosaic_dem_date(dem_groups_date,mosaic_yeardate_dir,'average', save_source=True, o_format='GTiff')
        dem_tif_list = mosaic_list

        # get valid pixel percentage
        dem_tif_list = check_dem_valid_per(dem_tif_list,mosaic_yeardate_dir,move_dem_threshold = keep_dem_percent)




    # co-registration


    # remove intermediate files
    if b_rm_inter:
        basic.outputlogMessage('remove intermediate files')
        for folder in tar_folders:
            io_function.delete_file_or_dir(folder)

    pass


if __name__ == "__main__":

    usage = "usage: %prog [options] extent_shp "
    parser = OptionParser(usage=usage, version="1.0 2020-12-26")
    parser.description = 'Introduction: get data list within an extent  '
    # parser.add_option("-x", "--save_xlsx_path",
    #                   action="store", dest="save_xlsx_path",
    #                   help="save the sence lists to xlsx file")


    parser.add_option("-a", "--ArcticDEM_dir",
                      action="store", dest="ArcticDEM_dir",default='./',
                      help="the folder saving downloaded ArcticDEM tarballs")

    parser.add_option("-d", "--save_dir",
                      action="store", dest="save_dir",default='./',
                      help="the folder to save pre-processed results")

    parser.add_option("-p", "--keep_dem_percent",
                      action="store", dest="keep_dem_percent",type=float,default=30.0,
                      help="keep dem with valid percentage greater than this value")

    parser.add_option("-m", "--create_mosaic_id",
                      action="store_true", dest="create_mosaic_id",default=False,
                      help="for a small region, if true, then get a mosaic of dem with the same ID (date_catalogID_catalogID)")

    parser.add_option("-t", "--create_mosaic_date",
                      action="store_true", dest="create_mosaic_date",default=False,
                      help="for a small region, if true, then get a mosaic of dem with close acquisition date ")

    parser.add_option("-r", "--remove_inter_data",
                      action="store_true", dest="remove_inter_data",default=False,
                      help="True to keep intermediate data")

    # there is one mosaic: Failed to compute statistics, no valid pixels found in sampling, other are ok,
    # so, may still use GTiff format.
    parser.add_option("-f", "--format",
                      action="store", dest="format", default='GTiff',  #default='VRT',
                      help="the data format for middle intermediate files")

    (options, args) = parser.parse_args()
    # print(options.create_mosaic)

    if len(sys.argv) < 2 or len(args) < 1:
        parser.print_help()
        sys.exit(2)

    main(options, args)
