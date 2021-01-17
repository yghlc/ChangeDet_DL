#!/usr/bin/env python
# Filename: check_reproject_dem_files 
"""
introduction:  check the projection for each region, reproject them if necessary

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 17 January, 2021
"""

import time
import os, sys
from optparse import OptionParser

HOME = os.path.expanduser('~')
codes_dir2 = HOME +'/codes/PycharmProjects/DeeplabforRS'
sys.path.insert(0, codes_dir2)

import basic_src.io_function as io_function
import basic_src.map_projection as map_projection
import basic_src.basic as basic
import parameters
import raster_io

def check_repoject_raster_list(para_file, para_name, target_image_list):
    raster_txt = parameters.get_string_parameters_None_if_absence(para_file,para_name)
    raster_list = io_function.read_list_from_txt(raster_txt)

    if len(raster_list) != len(target_image_list):
        raise ValueError('the number of rasters in %s is different from target inference image list'%raster_txt)

    output_list = []
    for t_img, raster in zip(target_image_list,raster_list):
        # check project
        target_prj = map_projection.get_raster_or_vector_srs_info_epsg(t_img)
        raster_prj = map_projection.get_raster_or_vector_srs_info_epsg(raster)

        # reproject if necessary
        if target_prj == raster_prj:
            return True
        else:
            xres, yres = raster_io.get_xres_yres_file(t_img)
            output = io_function.get_name_by_adding_tail(raster,'prj')
            map_projection.transforms_raster_srs(raster,target_prj,output,xres,yres,
                                                 compress='lzw',tiled='yes',bigtiff='if_safer')
            output_list.append(output)

        # update raster txt
        bak_txt = io_function.get_name_by_adding_tail(raster_txt,'bak')
        io_function.copy_file_to_dst(raster_txt,bak_txt)
        io_function.save_list_to_txt(raster_txt,output_list)

    return True

def main(options, args):
    para_file = args[0]
    inf_images_dir = parameters.get_string_parameters_None_if_absence(para_file,'inf_images_dir')
    inf_image_list = io_function.read_list_from_txt('inf_image_list.txt')

    t_image_list = io_function.read_list_from_txt(inf_image_list)
    t_image_list = [ os.path.join(inf_images_dir, item) for item in t_image_list]

    # dem
    check_repoject_raster_list(para_file,'multi_dem_files',t_image_list)

    # slop
    check_repoject_raster_list(para_file, 'multi_slope_files', t_image_list)

    # aspect
    # check_repoject_raster_list(para_file, 'multi_aspect_files', t_image_list)

    # dem diff
    check_repoject_raster_list(para_file, 'multi_dem_diff_files', t_image_list)

    # flow_accumulation


    pass

if __name__ == '__main__':
    usage = "usage: %prog [options] para.ini "
    parser = OptionParser(usage=usage, version="1.0 2021-01-17")
    parser.description = 'Introduction: check the projection for each region, reproject them if necessary '

    (options, args) = parser.parse_args()
    # print(options.to_rgb)
    if len(sys.argv) < 2 or len(args) < 1:
        parser.print_help()
        sys.exit(2)

    parameters.set_saved_parafile_path(args[0])

    main(options, args)


