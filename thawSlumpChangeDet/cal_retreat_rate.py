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
import vector_gpd
from vector_features import shape_opeation
import parameters


# local modules
# sys.path.insert(0, '../../lib/')
sys.path.insert(0,os.path.expanduser('~/codes/PycharmProjects/yghlc_Computational-Geometry/HW/lib'))
from polygon_medial_axis import compute_polygon_medial_axis, plot_polygon_medial_axis


import numpy as np
import matplotlib.pyplot as plt


def cal_expand_area_distance(expand_shp):
    '''
    calculate the distance of expanding areas along the upslope direction.
    The distance will save to expand_shp, backup it if necessary
    :param expand_shp: the shape file containing polygons which represent expanding areas of active thaw slumps
    :return: True if successful
    '''

    # read polygons
    # read polygons as shapely objects
    expand_polygons = vector_gpd.read_polygons_gpd(expand_shp)
    if len(expand_polygons) < 1:
        raise ValueError('No polygons in %s' % expand_shp)

    poly_min_Ws = []     #min_medAxis_width
    poly_max_Ws = []     #max_medAxis_width
    poly_mean_Ws = []    #mean_medAxis_width
    poly_median_Ws = []  #median_medAxis_width

    # go through each polygon, get its medial axis, then calculate distance.
    for idx, exp_polygon in enumerate(expand_polygons):

        basic.outputlogMessage('Calculating expanding distance of %dth (0 index) polygon'%idx)
        # if idx == 13:
        #     test = 1

        # for test
        # print(idx, exp_polygon)
        # print(exp_polygon)
        # if idx != 13:
        #     continue
        x_list, y_list = exp_polygon.exterior.coords.xy
        # xy = exp_polygon.exterior.coords
        vertices = [ (x,y) for (x,y) in zip(x_list,y_list)]
        vertices = np.array(vertices)
        # polygon_dis.append(idx*0.1)

        # h is used to sample points on bundary low h value, to reduce the number of points
        medial_axis, radiuses = compute_polygon_medial_axis(vertices, h=0.5)

        # for test
        # fig, ax = plt.subplots(figsize=(8, 8))
        # # plot_polygon_medial_axis(vertices, medial_axis, ax=ax)
        # plot_polygon_medial_axis(vertices, medial_axis, circ_radius=radiuses, draw_circle_idx=310, ax=ax)
        # ax.axis('equal')
        # ax.set_title('Medial Axis')
        # plt.show()
        # break

        # to 1d
        radiuses_1d = [value for item in radiuses for value in item]
        # remove redundant ones, if apply this, it not the mean and median value may change
        radiuses_noRed = set(radiuses_1d)
        np_rad_nored = np.array(list(radiuses_noRed))
        min_medAxis_width = np.min(np_rad_nored)
        max_medAxis_width = np.max(np_rad_nored)
        mean_medAxis_width = np.mean(np_rad_nored)
        median_medAxis_width = np.median(np_rad_nored)      # np median will take the average of the middle two if necessary

        poly_min_Ws.append(min_medAxis_width)
        poly_max_Ws.append(max_medAxis_width)
        poly_mean_Ws.append(mean_medAxis_width)
        poly_median_Ws.append(median_medAxis_width)


    # save the distance to shapefile
    shp_obj = shape_opeation()
    shp_obj.add_one_field_records_to_shapefile(expand_shp, poly_min_Ws, 'e_min_dis')
    shp_obj.add_one_field_records_to_shapefile(expand_shp, poly_max_Ws, 'e_max_dis')
    shp_obj.add_one_field_records_to_shapefile(expand_shp, poly_mean_Ws, 'e_mean_dis')
    shp_obj.add_one_field_records_to_shapefile(expand_shp, poly_median_Ws, 'e_medi_dis')

    basic.outputlogMessage('Save expanding distance of all the polygons to %s'%expand_shp)

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

    cal_expand_area_distance(args[0])

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