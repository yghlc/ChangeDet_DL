#!/usr/bin/env python
# Filename: get_annual_poly_change.py 
"""
introduction:  calculate the annual expansion of thaw slumps in Canadian Arctic

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 04 November, 2024
"""

import sys,os
from optparse import OptionParser

# added path of DeeplabforRS
sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import basic_src.io_function as io_function
import basic_src.basic as basic
import basic_src.map_projection as map_projection
import parameters


def main(options, args):

    # the shapefile, contain annual boundaries of thaw slumps
    in_shp_path = args[0]

    assert io_function.is_file_exist(in_shp_path)
    para_file = options.para_file



if __name__ == "__main__":
    usage = "usage: %prog [options] shapefile "
    parser = OptionParser(usage=usage, version="1.0 2024-11-04")
    parser.description = 'Introduction: conduct change detection for polygons (annual boundary of thaw slumps) '

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

    # set parameters files
    if options.para_file is None:
        print('error, no parameters file')
        parser.print_help()
        sys.exit(2)
    else:
        parameters.set_saved_parafile_path(options.para_file)

    basic.setlogfile('polygons_changeDetection.log')

    main(options, args)


