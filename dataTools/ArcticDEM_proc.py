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

import re
re_stripID='[0-9]{8}_[0-9A-F]{16}_[0-9A-F]{16}'


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
    b_mosaic = options.create_mosaic
    b_rm_inter = options.remove_inter_data

    # get tarball list
    tar_list = io_function.get_file_list_by_ext('.gz',tar_dir,bsub_folder=False)

    dem_folder_list = []
    dem_tif_list = []
    # unzip all of them, then  registration, crop
    crop_dir = os.path.join(save_dir, 'dem_stripID_crop')
    io_function.mkdir(crop_dir)
    for targz in tar_list:
        # file existence check
        tar_base = os.path.basename(targz)[:-7]
        files =  io_function.get_file_list_by_pattern(crop_dir,tar_base + '*')
        if len(files) == 1:
            basic.outputlogMessage('%s exist, skip processing tarball %s'%(files[0],targz))
            dem_tif_list.append(files[0])
            continue

        out_dir = io_function.unpack_tar_gz_file(targz,save_dir)
        if out_dir is not False:
            dem_folder_list.append(out_dir)
            dem_tif = os.path.join(out_dir, os.path.basename(out_dir) + '_dem.tif')
            if os.path.isfile(dem_tif):
                # registration for each DEM using dx, dy, dz in *reg.txt file
                reg_tif = dem_tif


                # crop and move to a new folder
                crop_tif = RSImageProcess.subset_image_by_shapefile(reg_tif, extent_shp)
                if crop_tif is False:
                    basic.outputlogMessage('warning, crop %s faild'%reg_tif)
                else:
                    new_crop_tif = os.path.join(crop_dir, os.path.basename(crop_tif))
                    io_function.move_file_to_dst(crop_tif,new_crop_tif)
                    dem_tif_list.append(new_crop_tif)
            else:
                basic.outputlogMessage('warning, no *_dem.tif in %s'%out_dir)

            # remove intermediate results
            if b_rm_inter:
                io_function.delete_file_or_dir(out_dir)

        # break


    # groups DEM
    dem_groups = {}
    for tif in dem_tif_list:
        strip_ids = re.findall(re_stripID, os.path.basename(tif))
        if len(strip_ids) != 1:
            print(strip_ids)
            raise ValueError('found zero or multiple strip IDs in %s, expect one'%tif)
        strip_id = strip_ids[0]
        if strip_id in dem_groups.keys():
            dem_groups[strip_id].append(tif)
        else:
            dem_groups[strip_id] = [tif]



    # create mosaic:
    mosaic_dir = os.path.join(save_dir,'dem_stripID_mosaic')
    if b_mosaic:
        io_function.mkdir(mosaic_dir)
        for key in dem_groups.keys():
            save_mosaic = os.path.join(mosaic_dir, key+'.tif')
            if len(dem_groups[key]) == 1:
                io_function.copy_file_to_dst(dem_groups[key][0],save_mosaic)
            else:
                # RSImageProcess.mosaics_images(dem_groups[key],save_mosaic)
                RSImageProcess.mosaic_crop_images_gdalwarp(dem_groups[key],save_mosaic,resampling_method='average')

        pass

    # co-registration

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

    parser.add_option("-m", "--create_mosaic",
                      action="store_true", dest="create_mosaic",default=False,
                      help="for a small region, if true, then get a mosaic of dem with the same ID (date_catalogID_catalogID)")

    parser.add_option("-r", "--remove_inter_data",
                      action="store_true", dest="remove_inter_data",default=False,
                      help="True to keep intermediate data")

    (options, args) = parser.parse_args()
    # print(options.create_mosaic)

    if len(sys.argv) < 2 or len(args) < 1:
        parser.print_help()
        sys.exit(2)

    main(options, args)
