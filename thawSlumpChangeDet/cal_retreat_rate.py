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
import basic_src.io_function as io_function
import vector_gpd
from vector_features import shape_opeation
import parameters

import random
import math

# local modules
# sys.path.insert(0, '../../lib/')
sys.path.insert(0,os.path.expanduser('~/codes/PycharmProjects/yghlc_Computational-Geometry/HW/lib'))
from polygon_medial_axis import compute_polygon_medial_axis, plot_polygon_medial_axis


import numpy as np


class get_medial_axis_class(object):
    def __init__(self):
        pass

    def __del__(self):
        pass

    def ref_compute_polygon_medial_axis(self, vertices, h=0.5):
        return compute_polygon_medial_axis(vertices, h=h)

def get_medial_axis_of_one_polygon(vertices, h=0.5):
    '''
    due to the unstable codes (error of interrupted by signal 11: SIGSEGV)
    we try to call the script to get result
    :param vertices:
    :param h:
    :return:
    '''

    # save the vertices to files
    tmp_polygon_txt = 'out_polygon_vertices.txt'
    tmp_medial_axis_txt = 'save_medial_axis_radius.txt'
    if os.path.isfile(tmp_polygon_txt):
        io_function.delete_file_or_dir(tmp_polygon_txt)
    if os.path.isfile(tmp_medial_axis_txt):
        io_function.delete_file_or_dir(tmp_medial_axis_txt)

    ## not necessary, previously, the error is due to its small area, not the triangular shape
    # new_vertices = []
    # if len(vertices) < 5: # for a triangle
    #     basic.outputlogMessage('Warning, insert some points for a triangle')
    #     # manually added some points
    #     for idx in range(len(vertices)-1):
    #         new_vertices.append(vertices[idx])
    #         a_new_point = ((vertices[idx][0] + vertices[idx+1][0])/2.0,
    #                        (vertices[idx][1] + vertices[idx + 1][1]) / 2.0)
    #         new_vertices.append(a_new_point)
    #     new_vertices.append(vertices[-1])
    #     vertices = np.array(new_vertices)

    res = np.savetxt(tmp_polygon_txt,vertices)
    # print(res)

    # call the script to
    script = os.path.expanduser('~/codes/PycharmProjects/yghlc_Computational-Geometry/HW/project/code/medial_axis_outRadius.py')

    # if script crash, then try again, with a differnt h value
    while os.path.isfile(tmp_medial_axis_txt) is False:
        args_list = [script, tmp_polygon_txt, str(h)]
        if basic.exec_command_args_list_one_file(args_list, tmp_medial_axis_txt) is False:
            basic.outputlogMessage('failed to get medial axis and radius, change h value, then try again')
            h = h - 0.05
        if os.path.isfile(tmp_medial_axis_txt) and os.path.getsize(tmp_medial_axis_txt) < 1:
            print('fileSize:',os.path.getsize(tmp_medial_axis_txt))
            io_function.delete_file_or_dir(tmp_medial_axis_txt)
            h = h - 0.05
        if h < 0.1:
            h = random.uniform(0.01, 0.1)

    if os.path.isfile(tmp_medial_axis_txt) is False:
        raise ValueError('error, failed to get medial axis and radius')

    # read result from file
    medial_axis_radiuses = np.loadtxt(tmp_medial_axis_txt)
    if medial_axis_radiuses.ndim == 1:      # if the result has only one row, change to 2 dimision
        medial_axis_radiuses = medial_axis_radiuses.reshape(1,medial_axis_radiuses.shape[0])
    print(medial_axis_radiuses.shape)
    medial_axis = []
    radiuses = []
    for row in medial_axis_radiuses:
        x1, y1, x2, y2, r1, r2 = row
        medial_axis.append(((x1,y1),(x2,y2)))
        radiuses.append((r1,r2))
    return medial_axis, radiuses

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

        basic.outputlogMessage('Calculating expanding distance of %dth (0 index) polygon, total: %d'%(idx,len(expand_polygons)))
        # if idx == 13:
        #     test = 1

        if exp_polygon.area < 1:
            # for a small polygon, it may failed to calculate its radiues, so get a approximation values
            basic.outputlogMessage('The polygon is very small (area < 1), use sqrt(area/pi) as its radius')
            radiuses = np.array([[math.sqrt(exp_polygon.area/math.pi)]])
        else:

            # for test
            # print(idx, exp_polygon)
            # print(exp_polygon)
            # if idx < 13 or idx==55:
            #     continue
            x_list, y_list = exp_polygon.exterior.coords.xy
            # xy = exp_polygon.exterior.coords
            vertices = [ (x,y) for (x,y) in zip(x_list,y_list)]
            vertices = np.array(vertices)
            # polygon_dis.append(idx*0.1)

            ############################ This way to call compute_polygon_medial_axis is unstale, sometime, it has error of:
            ### Process finished with exit code 139 (interrupted by signal 11: SIGSEGV)
            # medial_axis_obj = get_medial_axis_class()
            # h is used to sample points on bundary low h value, to reduce the number of points
            # medial_axis, radiuses = compute_polygon_medial_axis(vertices, h=0.5)
            # medial_axis, radiuses = medial_axis_obj.ref_compute_polygon_medial_axis(vertices, h=0.5)
            # medial_axis_obj = None
            # try:
            #     medial_axis, radiuses = compute_polygon_medial_axis(vertices, h=0.5)
            # except Exception as e:  # can get all the exception, and the program will not exit
            #     basic.outputlogMessage('unknown error: ' + str(e))
            ####################################################################################

            # interrupted by signal 11: SIGSEGV or segmentation fault may be avoid if change the h value
            medial_axis, radiuses = get_medial_axis_of_one_polygon(vertices, h=0.3)


            ## for test
            # avoid import matplotlib if don't need it, or it will ask for graphic environment, and make window loses focus
            # import matplotlib.pyplot as plt
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

        poly_min_Ws.append(min_medAxis_width*2) # multiply by 2, then it is diameter
        poly_max_Ws.append(max_medAxis_width*2)
        poly_mean_Ws.append(mean_medAxis_width*2)
        poly_median_Ws.append(median_medAxis_width*2)

        # break

    ## save the distance to shapefile
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