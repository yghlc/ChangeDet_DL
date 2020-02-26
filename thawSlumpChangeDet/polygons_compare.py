#!/usr/bin/env python
# Filename: polygons_cd 
"""
introduction: compare two polygons in to shape file

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 26 February, 2020
"""

import sys,os
from optparse import OptionParser

# added path of DeeplabforRS
sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import basic_src.io_function as io_function
import basic_src.basic as basic
import basic_src.map_projection as map_projection
import parameters

import polygons_cd_multi
import polygons_cd

def main(options, args):

    old_shp_path = args[0]
    new_shp_path = args[1]

    # check files do exist
    assert io_function.is_file_exist(new_shp_path)
    assert io_function.is_file_exist(old_shp_path)

    # check projection of the shape file, should be the same
    old_shp_proj4 = map_projection.get_raster_or_vector_srs_info_proj4(old_shp_path)
    new_shp_proj4 = map_projection.get_raster_or_vector_srs_info_proj4(new_shp_path)

    if old_shp_proj4 != new_shp_proj4:
        raise ValueError('error, projection insistence between %s and %s' % (old_shp_proj4, new_shp_proj4))

    main_shp_name = polygons_cd_multi.get_main_shp_name(old_shp_path,new_shp_path)

    # conduct change detection
    if options.output is None:
        output_path = 'change_'+ main_shp_name
    else:
        output_path = options.output

    basic.outputlogMessage('Conduct change detection on %s and %s, and the results will be saved to %s'%
                           (old_shp_path, new_shp_path, output_path))

    # get expanding and shrinking parts
    output_path_expand = 'expand_' + main_shp_name
    output_path_shrink = 'shrink_' + main_shp_name
    polygons_cd.polygons_change_detection(old_shp_path, new_shp_path, output_path_expand,output_path_shrink)



if __name__ == "__main__":
    usage = "usage: %prog [options] old_shape_file new_shape_file "
    parser = OptionParser(usage=usage, version="1.0 2020-02-26")
    parser.description = 'Introduction: compare two groups of polygons '

    parser.add_option("-p", "--para",
                      action="store", dest="para_file",
                      help="the parameters file")

    parser.add_option('-o', '--output',
                      action="store", dest = 'output',
                      help='the path to save the change detection results')

    (options, args) = parser.parse_args()
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(2)

    # # set parameters files
    # if options.para_file is None:
    #     print('error, no parameters file')
    #     parser.print_help()
    #     sys.exit(2)
    # else:
    #     parameters.set_saved_parafile_path(options.para_file)

    basic.setlogfile('polygons_changeDetection.log')

    main(options, args)



