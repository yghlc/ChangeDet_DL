#!/usr/bin/env python
# Filename: cal_relative_dem 
"""
introduction: to calculate the relative elevation for change polygons.
# the elevation of change polygons, comparing with the elevation of old thaw slumps,
# a higher elevation indicates at a upslope location.

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 02 February, 2020
"""

import sys,os
from optparse import OptionParser

sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import basic_src.basic as basic

def main(options, args):

    

    pass




if __name__ == "__main__":
    usage = "usage: %prog [options] change_polygon.shp dem.tif"
    parser = OptionParser(usage=usage, version="1.0 2020-01-31")
    parser.description = 'Introduction: calculate the relative elevation for change polygons '

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