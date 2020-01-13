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
    os.system('mkdir -p ' + os.path.join(saved_dir, 'subImages'))
    os.system('mkdir -p ' + os.path.join(saved_dir, 'subLabels'))
    dstnodata = options.dstnodata
    if 'qtb_sentinel2' in image_tile_list[0]:
        # for qtb_sentinel-2 mosaic
        pre_name = '_'.join(os.path.splitext(os.path.basename(image_tile_list[0]))[0].split('_')[:4])
    else:
        pre_name = os.path.splitext(os.path.basename(image_tile_list[0]))[0]
    get_sub_images_and_labels(t_polygons_shp, t_polygons_shp_all, bufferSize, image_tile_list,
                              saved_dir, pre_name, dstnodata, brectangle=options.rectangle)


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