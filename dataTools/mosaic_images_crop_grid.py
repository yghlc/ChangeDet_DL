#!/usr/bin/env python
# Filename: mosaic_images_crop_grid 
"""
introduction: create mosaic of many small images and crop to grid

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 19 July, 2020
"""
import sys,os
from optparse import OptionParser
import re

sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import basic_src.io_function as io_function
import basic_src.basic as basic
import basic_src.map_projection as map_projection
import basic_src.RSImageProcess as RSImageProcess
import vector_gpd
from datetime import datetime


# sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/ChangeDet_DL/dataTools'))
from  get_planet_image_list import  get_Planet_SR_image_list_overlap_a_polygon

prePlanetImage = os.path.expanduser('~/codes/PycharmProjects/Landuse_DL/planetScripts/prePlanetImage.py')

def convert_planet_to_rgb_images(tif_path,save_dir='RGB_images'):

    if os.path.isdir(save_dir) is False:
        io_function.mkdir(save_dir)

    # filename_no_ext
    output = os.path.splitext(os.path.basename(tif_path))[0]
    fin_output= os.path.join(save_dir, output + '_8bit_rgb_sharpen.tif')
    if os.path.isfile(fin_output):
        basic.outputlogMessage("Skip, because File %s exists in current folder: %s"%(fin_output,os.getcwd()))
        return fin_output

    # use fix min and max to make the color be consistent to sentinel-images
    src_min=0
    src_max=3000
    dst_min=1       # 0 is the nodata, so set as 1
    dst_max=255

    # gdal_translate -ot Byte -scale ${src_min} ${src_max} ${dst_min} ${dst_max} ${image_path} ${output}_8bit.tif
    cmd_str = 'gdal_translate -ot Byte -scale %d %d %d %d %s %s_8bit.tif'%(src_min,src_max,dst_min,dst_max,tif_path,output)
    status, result = basic.exec_command_string(cmd_str)
    if status != 0:
        print(result)
        sys.exit(status)

    # the third band is red, second is green, and first is blue
    #gdal_translate -b 3 -b 2 -b 1  ${output}_8bit.tif ${output}_8bit_rgb.tif
    cmd_str = 'gdal_translate -b 3 -b 2 -b 1  %s_8bit.tif %s_8bit_rgb.tif'%(output,output)
    status, result = basic.exec_command_string(cmd_str)
    if status != 0:
        print(result)
        sys.exit(status)

    # python ${code_dir}/planetScripts/prePlanetImage.py ${output}_8bit_rgb.tif ${fin_output}
    cmd_str = 'python %s %s_8bit_rgb.tif %s'%(prePlanetImage,output,fin_output)
    status, result = basic.exec_command_string(cmd_str)
    if status != 0:
        print(result)
        sys.exit(status)

    # set nodata
    # gdal_edit.py -a_nodata 0  ${fin_output}
    cmd_str = 'gdal_edit.py -a_nodata 0  %s' % fin_output
    status, result = basic.exec_command_string(cmd_str)
    if status != 0:
        print(result)
        sys.exit(status)

    io_function.delete_file_or_dir('%s_8bit.tif'%output)
    io_function.delete_file_or_dir('%s_8bit_rgb.tif'%output)

    return fin_output


def create_moasic_of_each_grid_polygon(id,polygon, polygon_latlon, out_res, cloud_cover_thr, geojson_list, save_dir, to_rgb=True, nodata=0):
    '''
    create mosaic for Planet images within a grid
    :param polygon:
    :param polygon_latlon:
    :param out_res:
    :param cloud_cover_thr:
    :param geojson_list:
    :param save_dir:
    :param to_rgb:
    :param nodata:
    :return:
    '''
    # get image list and cloud cover
    planet_img_list, cloud_covers = get_Planet_SR_image_list_overlap_a_polygon(polygon_latlon,geojson_list,cloud_cover_thr)
    if len(planet_img_list) < 1:
        basic.outputlogMessage('warning, no images within %d grid'%id)
        return False

    print('images and their cloud cover for %dth grid:'%id)
    for img, cloud_cover in zip(planet_img_list, cloud_covers):
        print(img, cloud_cover)

    # convert to RGB images (for Planet)
    rgb_image_list = []
    if to_rgb:
        for tif_path in planet_img_list:
            rgb_img = convert_planet_to_rgb_images(tif_path)
            rgb_image_list.append(rgb_img)
    if len(rgb_image_list) > 0:
        planet_img_list = rgb_image_list

    # create mosaic using gdal_merge.py
    # because in gdal_merge.py, a later image will replace one, so we put image with largest cloud cover first
    file_name = os.path.basename(save_dir)
    out = os.path.join(save_dir,file_name + '_sub_%d_tmp.tif'%id)
    if os.path.isfile(out):
        io_function.delete_file_or_dir(out)

    # reverse=True to make it in descending order
    img_cloud_list = [(img_path,cloud) for cloud, img_path in sorted(zip(cloud_covers,planet_img_list), key=lambda pair: pair[0],reverse=True)]
    # for checking
    print('Image and its cloud after sorting:')
    for (img_path,cloud)  in img_cloud_list:
        print(img_path,cloud)
    tifs = [img_path for (img_path,cloud)  in img_cloud_list ]
    tifs_str = ' '.join(tifs)

    cmd_str = 'gdal_merge.py -o %s -n %d -init %d -ps %d %d %s'%(out,nodata,nodata,out_res,out_res,tifs_str)
    status, result = basic.exec_command_string(cmd_str)
    if status != 0:
        print(result)
        sys.exit(status)

    # crop
    fin_out = os.path.join(save_dir,file_name + '_sub_%d.tif'%id)
    # #  polygon.exterior.coords
    minx, miny, maxx, maxy =  polygon.bounds    # (minx, miny, maxx, maxy)
    print(minx, miny, maxx, maxy)
    results = RSImageProcess.subset_image_projwin(fin_out,out,minx, maxy, maxx, miny, xres=out_res,yres=out_res)
    print(results)

    io_function.delete_file_or_dir(out)

    # sys.exit(0)

    return fin_out


def main(options, args):

    image_dir = args[0]
    geojson_list = io_function.get_file_list_by_ext('.geojson',image_dir,bsub_folder=True)
    if len(geojson_list) < 1:
        raise ValueError('There is no geojson files in %s'%image_dir)

    basic.outputlogMessage('Image Dir: %s'%image_dir)

    grid_polygon_shp = args[1]      # the polygon should be in projection Cartesian coordinate system (e.g., UTM )
    basic.outputlogMessage('Image grid polygon shapefile: %s' % grid_polygon_shp)

    # read grid polygons
    grid_polygons = vector_gpd.read_polygons_gpd(grid_polygon_shp)
    grid_ids = vector_gpd.read_attribute_values_list(grid_polygon_shp,'id')

    shp_prj = map_projection.get_raster_or_vector_srs_info_proj4(grid_polygon_shp).strip()
    # print(shp_prj)
    grid_polygons_latlon = grid_polygons
    if shp_prj != '+proj=longlat +datum=WGS84 +no_defs':
        # read polygons and reproject to 4326 projection
        grid_polygons_latlon = vector_gpd.read_shape_gpd_to_NewPrj(grid_polygon_shp,'EPSG:4326')

    # create mosaic of each grid
    cloud_cover_thr = options.cloud_cover
    cloud_cover_thr = cloud_cover_thr * 100         # for Planet image, it is percentage
    out_res = options.out_res
    cur_dir = os.getcwd()
    save_dir = os.path.basename(cur_dir) + '_mosaic_' + str(out_res)
    # print(save_dir)
    io_function.mkdir(save_dir)
    for id, polygon, poly_latlon in zip(grid_ids,grid_polygons,grid_polygons_latlon):
        create_moasic_of_each_grid_polygon(id, polygon, poly_latlon, out_res,
                                           cloud_cover_thr, geojson_list,save_dir)

        pass

    #


    pass

if __name__ == "__main__":

    usage = "usage: %prog [options] image_dir polygon_shp "
    parser = OptionParser(usage=usage, version="1.0 2020-07-19")
    parser.description = 'Introduction: create mosaic of Planet images and save to files '
    # parser.add_option("-s", "--start_date",default='2018-04-30',
    #                   action="store", dest="start_date",
    #                   help="start date for inquiry, with format year-month-day, e.g., 2018-05-23")
    # parser.add_option("-e", "--end_date",default='2018-06-30',
    #                   action="store", dest="end_date",
    #                   help="the end date for inquiry, with format year-month-day, e.g., 2018-05-23")
    parser.add_option("-c", "--cloud_cover",
                      action="store", dest="cloud_cover", type=float,default=0.3,
                      help="the could cover threshold, only accept images with cloud cover less than the threshold")
    parser.add_option("-r", "--out_res",
                      action="store", dest="out_res", type=float,default=30,
                      help="the output resolution of mosaic")
    # parser.add_option("-i", "--item_types",
    #                   action="store", dest="item_types",default='PSScene4Band',
    #                   help="the item types, e.g., PSScene4Band,PSOrthoTile")
    # parser.add_option("-a", "--planet_account",
    #                   action="store", dest="planet_account",default='huanglingcao@link.cuhk.edu.hk',
    #                   help="planet email account, e.g., huanglingcao@link.cuhk.edu.hk")



    (options, args) = parser.parse_args()
    if len(sys.argv) < 2 or len(args) < 1:
        parser.print_help()
        sys.exit(2)

    basic.setlogfile('mosaic_images_crop_grid_%s.log'%str(datetime.date(datetime.now())))

    main(options, args)