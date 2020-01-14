#!/usr/bin/env python
# Filename: get_subimage_pairs 
"""
introduction: get pairs of sub-images for change detection

The change polygons: for each polygon, in its buffer area (defined by the input parameters), it should identify all the expanding of thaw slumps

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 13 January, 2020
"""

import sys,os
from optparse import OptionParser

sys.path.insert(0,os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import basic_src.io_function as io_function
import basic_src.basic as basic

sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/Landuse_DL'))
from sentinelScripts.get_subImages import get_sub_image
from sentinelScripts.get_subImages import get_sub_label
from sentinelScripts.get_subImages import get_projection_proj4
from sentinelScripts.get_subImages import check_projection_rasters
from sentinelScripts.get_subImages import meters_to_degress_onEarth
from sentinelScripts.get_subImages import get_image_tile_bound_boxes

# import thest two to make sure load GEOS dll before using shapely
import shapely
import shapely.geometry

import geopandas as gpd

def get_file_prename(ref_file_name):

    if 'qtb_sentinel2' in ref_file_name:
        # for qtb_sentinel-2 mosaic
        pre_name = '_'.join(os.path.splitext(os.path.basename(ref_file_name))[0].split('_')[:4])
    else:
        pre_name = os.path.splitext(os.path.basename(ref_file_name))[0]

    return pre_name

def get_image_pair_and_change_map(t_polygons_shp, t_polygons_shp_all, bufferSize, old_image_tile_list, new_image_tile_list, saved_dir, dstnodata, brectangle = True):
    '''
    get sub image pairs (and labels, as know as change map ) from training polygons
    :param t_polygons_shp: training polygon
    :param t_polygons_shp_all: the full set of training polygon, t_polygons_shp is a subset or equal to this one.
    :param bufferSize: buffer size of a center polygon to create a sub images
    :param old_image_tile_list: old image tiles
    :param new_image_tile_list: new image tiles
    :param saved_dir: output dir
    :param dstnodata: nodata when save for the output images
    :param brectangle: True: get the rectangle extent of a images.
    :return:
    '''

    # read polygons
    t_shapefile = gpd.read_file(t_polygons_shp)
    class_labels = t_shapefile['ChangeType'].tolist()
    center_polygons = t_shapefile.geometry.values
    # check_polygons_invalidity(center_polygons,t_polygons_shp)

    # read the full set of training polygons, used this one to produce the label images
    t_shapefile_all = gpd.read_file(t_polygons_shp_all)
    class_labels_all = t_shapefile_all['ChangeType'].tolist()
    polygons_all = t_shapefile_all.geometry.values
    # check_polygons_invalidity(polygons_all,t_polygons_shp_all)

    old_img_tile_boxes = get_image_tile_bound_boxes(old_image_tile_list)
    new_img_tile_boxes = get_image_tile_bound_boxes(new_image_tile_list)

    pre_name_oldImg = get_file_prename(old_image_tile_list[0])
    pre_name_newImg = get_file_prename(new_image_tile_list[0])
    pre_name_for_label = os.path.splitext(os.path.basename(t_polygons_shp))[0]

    list_txt_obj = open('pair_images_chnagemap_list.txt','a')
    # go through each polygon
    for idx, (c_polygon, c_class_int) in enumerate(zip(center_polygons,class_labels)):

        # output message
        basic.outputlogMessage('obtaining %dth sub-image and the change map raster'%idx)

        # get buffer area
        expansion_polygon = c_polygon.buffer(bufferSize)

        # get one old sub-image based on the buffer areas
        old_subimg_shortName = os.path.join('img_pairs' , pre_name_oldImg+'_%d_ChangeType_%d.tif'%(idx,c_class_int))
        old_subimg_saved_path = os.path.join(saved_dir, old_subimg_shortName)
        if get_sub_image(idx,expansion_polygon,old_image_tile_list,old_img_tile_boxes, old_subimg_saved_path, dstnodata, brectangle) is False:
            basic.outputlogMessage('Warning, skip the %dth polygon for generating the old sub-image'%idx)
            continue

        # get one old sub-image based on the buffer areas
        new_subimg_shortName = os.path.join('img_pairs' , pre_name_newImg+'_%d_ChangeType_%d.tif'%(idx,c_class_int))
        new_subimg_saved_path = os.path.join(saved_dir, new_subimg_shortName)
        if get_sub_image(idx,expansion_polygon,new_image_tile_list,new_img_tile_boxes, new_subimg_saved_path, dstnodata, brectangle) is False:
            basic.outputlogMessage('Warning, skip the %dth polygon for generating the new sub-image'%idx)
            continue

        # based on the sub-image, create the corresponding vectors
        sublabel_shortName = os.path.join('change_maps', pre_name_for_label + '_%d_ChangeType_%d.tif' % (idx, c_class_int))
        sublabel_saved_path = os.path.join(saved_dir, sublabel_shortName)
        if get_sub_label(idx,new_subimg_saved_path, c_polygon, c_class_int, polygons_all, class_labels_all, bufferSize, brectangle, sublabel_saved_path) is False:
            basic.outputlogMessage('Warning, get the label raster for %dth polygon failed' % idx)
            continue

        list_txt_obj.writelines(old_subimg_shortName+":"+new_subimg_shortName + ":"+sublabel_shortName+'\n')


    list_txt_obj.close()

    pass


def main(options, args):

    change_poly_path = args[0]
    old_img_folder = args[1]
    new_img_folder = args[2]

    # check file exist
    assert io_function.is_file_exist(change_poly_path)

    t_polygons_shp_all = options.all_training_polygons
    if t_polygons_shp_all is None:
        basic.outputlogMessage('Warning, the full set of training polygons is not assigned, '
                               'it will consider the one in input argument is the full set of training polygons')
        t_polygons_shp_all = change_poly_path
    else:
        if get_projection_proj4(change_poly_path) != get_projection_proj4(t_polygons_shp_all):
            raise ValueError('error, projection insistence between %s and %s' % (change_poly_path, t_polygons_shp_all))
        assert io_function.is_file_exist(t_polygons_shp_all)

    # get image tile list
    # image_tile_list = io_function.get_file_list_by_ext(options.image_ext, image_folder, bsub_folder=False)
    old_images_list = io_function.get_file_list_by_pattern(old_img_folder, options.image_ext)
    new_images_list = io_function.get_file_list_by_pattern(new_img_folder, options.image_ext)
    if len(old_images_list) < 1:
        raise IOError('error, failed to get image tiles in folder %s' % old_img_folder)
    if len(new_images_list) < 1:
        raise IOError('error, failed to get image tiles in folder %s' % new_img_folder)

    check_projection_rasters(old_images_list)  # it will raise errors if found problems
    check_projection_rasters(new_images_list)  # it will raise errors if found problems

    # need to check: the shape file and raster should have the same projection.
    if get_projection_proj4(change_poly_path) != get_projection_proj4(old_images_list[0]):
        raise ValueError('error, the input raster (e.g., %s) and vector (%s) files don\'t have the same projection' % (
            old_images_list[0], change_poly_path))
    if get_projection_proj4(change_poly_path) != get_projection_proj4(new_images_list[0]):
        raise ValueError('error, the input raster (e.g., %s) and vector (%s) files don\'t have the same projection' % (
            new_images_list[0], change_poly_path))

    # check these are EPSG:4326 projection
    if get_projection_proj4(change_poly_path).strip() == '+proj=longlat +datum=WGS84 +no_defs':
        bufferSize = meters_to_degress_onEarth(options.bufferSize)
    else:
        bufferSize = options.bufferSize

    saved_dir = options.out_dir
    os.system('mkdir -p ' + os.path.join(saved_dir, 'img_pairs'))
    os.system('mkdir -p ' + os.path.join(saved_dir, 'change_maps'))
    dstnodata = options.dstnodata

    get_image_pair_and_change_map(change_poly_path, t_polygons_shp_all, bufferSize, old_images_list, new_images_list,
                              saved_dir, dstnodata, brectangle=options.rectangle)


    pass



if __name__ == "__main__":
    usage = "usage: %prog [options] change_polygons old_image_folder new_image_folder"
    parser = OptionParser(usage=usage, version="1.0 2020-1-13")
    parser.description = 'Introduction: get sub Images (and Labels) from multi-temporal images for change detection. ' \
                         'The images and shape file should have the same projection.'
    parser.add_option("-f", "--all_training_polygons",
                      action="store", dest="all_training_polygons",
                      help="the full set of training polygons for change detection. If the one in the input argument "
                           "is a subset of training polygons, this one must be assigned")
    parser.add_option("-b", "--bufferSize",
                      action="store", dest="bufferSize",type=float,
                      help="buffer size is in the projection, normally, it is based on meters")
    parser.add_option("-e", "--image_ext",
                      action="store", dest="image_ext",default = '*.tif',
                      help="the image pattern of the image file")
    parser.add_option("-o", "--out_dir",
                      action="store", dest="out_dir",
                      help="the folder path for saving output files")
    parser.add_option("-n", "--dstnodata", type=int,
                      action="store", dest="dstnodata",
                      help="the nodata in output images")
    parser.add_option("-r", "--rectangle",
                      action="store_true", dest="rectangle",default=False,
                      help="whether use the rectangular extent of the polygon")


    (options, args) = parser.parse_args()
    if len(sys.argv) < 2 or len(args) < 1:
        parser.print_help()
        sys.exit(2)

    # if options.para_file is None:
    #     basic.outputlogMessage('error, parameter file is required')
    #     sys.exit(2)

    main(options, args)