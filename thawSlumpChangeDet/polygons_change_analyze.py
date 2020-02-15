#!/usr/bin/env python
# Filename: polygons_change_analyze
"""
introduction: run polygons based change analysis for a series of multi-temporal polygons (from manual delineation or automatic mapping)

try to output info that,

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 15 February, 2020
"""

import sys,os
from optparse import OptionParser

# added path of DeeplabforRS
sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import basic_src.basic as basic

import parameters

# sys.path.insert(0, os.path.dirname(__file__))


def main(options, args):

    # for oldest to newest
    polyon_shps_list = [item for item in args]
    print(polyon_shps_list)

    para_file = options.para_file

    for idx in range(len(polyon_shps_list)-1):
        # print(idx)
        # get_expanding_change(polyon_shps_list[idx], polyon_shps_list[idx+1], para_file)

        pass



    pass

if __name__ == "__main__":
    usage = "usage: %prog [options] polygons1.shp polygon2.shp ... (from oldest to newest) "
    parser = OptionParser(usage=usage, version="1.0 2020-02-09")
    parser.description = 'Introduction: conduct change analysis on multi-temporal polygons '

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

    basic.setlogfile('polygons_changeAnalysis.log')

    main(options, args)




