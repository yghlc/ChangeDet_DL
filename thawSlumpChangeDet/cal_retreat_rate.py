#!/usr/bin/env python
# Filename: cal_retreat_rate 
"""
introduction: to calculate the retreat rates of thaw slumps, from polygons.



authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 31 January, 2020
"""

import sys,os
from optparse import OptionParser

# added path of DeeplabforRS
sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import basic_src.basic as basic
import parameters


# local modules
# sys.path.insert(0, '../../lib/')
sys.path.insert(0,os.path.expanduser('~/codes/PycharmProjects/yghlc_Computational-Geometry/HW/lib'))
from polygon_medial_axis import compute_polygon_medial_axis, plot_polygon_medial_axis

# import basic_src.map_projection as map_projection
# import basic_src.io_function as io_function



def cal_expand_area_distance(expand_shp):
    '''
    calculate the distance of expanding areas along the upslope direction.
    The distance will save to expand_shp, backup it if necessary
    :param expand_shp: the shape file containing polygons which represent expanding areas of active thaw slumps
    :return: True if successful
    '''

    # read polygons

    #
    



    return True

def main(options, args):

    # # a test of compute_polygon_medial_axis
    # import numpy as np
    # import matplotlib.pyplot as plt
    # polygon = np.loadtxt("polygon_2.txt") #sys.argv[1], polygon_1.txt, polygon_2.txt
    # fig, ax = plt.subplots(figsize=(8, 8))
    # medial_axis = compute_polygon_medial_axis(polygon, h=0.1)   # it seems that smaller h can output detailed medial axis.
    # plot_polygon_medial_axis(polygon, medial_axis, ax=ax)
    # ax.axis('equal')
    # ax.set_title('Medial Axis')
    # plt.show()


    pass



if __name__ == "__main__":
    usage = "usage: %prog [options]  change_polygon.shp "
    parser = OptionParser(usage=usage, version="1.0 2020-01-31")
    parser.description = 'Introduction: calculate the retreat rates of thaw slumps based on their expanding areas '

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