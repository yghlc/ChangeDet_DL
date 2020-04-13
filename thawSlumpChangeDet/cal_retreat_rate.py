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
import basic_src.RSImage as RSImage
from basic_src.RSImage import RSImageclass

import random
import math

# local modules
# sys.path.insert(0, '../../lib/')
sys.path.insert(0,os.path.expanduser('~/codes/PycharmProjects/yghlc_Computational-Geometry/HW/lib'))
from polygon_medial_axis import compute_polygon_medial_axis, plot_polygon_medial_axis


import numpy as np

import multiprocessing
from multiprocessing import Pool

import shapely
from shapely.geometry import LineString
from shapely.geometry import Point

class get_medial_axis_class(object):
    def __init__(self):
        pass

    def __del__(self):
        pass

    def ref_compute_polygon_medial_axis(self, vertices, h=0.5):
        return compute_polygon_medial_axis(vertices, h=h)

def get_projection_proj4(geo_file):
    '''
    get the proj4 string
    :param geo_file: a shape file or raster file
    :return: projection string in prj4 format
    '''
    import basic_src.map_projection as map_projection
    return map_projection.get_raster_or_vector_srs_info_proj4(geo_file)

def get_medial_axis_of_one_polygon(vertices, h=0.5, proc_id=0):
    '''
    due to the unstable codes (error of interrupted by signal 11: SIGSEGV)
    we try to call the script to get result
    :param vertices:
    :param h:
    :return:
    '''

    # save the vertices to files
    tmp_polygon_txt = 'out_polygon_vertices_%d.txt'%proc_id
    tmp_medial_axis_txt = 'save_medial_axis_radius_%d.txt'%proc_id
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
    return medial_axis, radiuses, h

def meidal_circles_segment(exp_polygon,a_medial_axis, radius,dem_path, dem_res):

    (x1, y1), (x2, y2) = a_medial_axis  # (x1, y1) and (x2, y2) are close to each other
    r1, r2 = radius

    # use the one with larger radius
    x0, y0, r = x1, y1, r1
    if r2 > r1:
        x0, y0, r = x2, y2, r2

    # for (x0,y0), r in zip(a_medial_axis, radius):

    center_point = Point(x0,y0)
    # half length of the line segment for calculating elevation difference
    line_half_len_for_dem = r + dem_res

    diff_ele_list = []
    angle_list = []
    for angle in range(0, 180):
        # construct a line
        rad = math.radians(angle)
        dx = line_half_len_for_dem*math.cos(rad)
        dy = line_half_len_for_dem*math.sin(rad)

        xs = x0 + dx
        ys = y0 + dy
        xe = x0 - dx
        ye = y0 - dy

        # get elevation difference
        ele_s = RSImage.get_image_location_value(dem_path,xs,ys,'prj',1)
        ele_e = RSImage.get_image_location_value(dem_path,xe,ye,'prj',1)
        diff_ele = abs(ele_s - ele_e)

        diff_ele_list.append(diff_ele)
        angle_list.append(angle)

    # find the maximum elevation difference (could have multiple values)
    max_diff_eles = max(diff_ele_list)
    max_d_ele_index_list =  [i for i, x in enumerate(diff_ele_list) if x == max_diff_eles]

    box = exp_polygon.bounds
    line_half_len_for_interset = max(abs(box[2]-box[0]), abs(box[3] - box[1]))/2.0
    inter_line_length = []
    for index in max_d_ele_index_list:
        # construct a line
        rad = math.radians(angle_list[index])
        dx = line_half_len_for_interset * math.cos(rad)
        dy = line_half_len_for_interset * math.sin(rad)

        xs = x0 + dx
        ys = y0 + dy
        xe = x0 - dx
        ye = y0 - dy

        line = LineString([(xs, ys), (xe, ye)])
        # may have multiple lines, only chose the one intersec with (x0,y0)
        inter_lines = line.intersection(exp_polygon)
        if inter_lines.geom_type == 'LineString':
            pass
        elif inter_lines.geom_type == 'MultiLineString':
            # convert MultiLineString to LineString
            for a_line in list(inter_lines):
                # print(a_line)
                # print(a_line.buffer(0.1).intersection(center_point))
                # only one line will intersect with the center point
                if a_line.buffer(0.1).intersection(center_point).is_empty:
                    continue
                else:
                    inter_lines = a_line
                    break
            # test = 1
        else:
            # if there are multiple lines, need to find the one intersect with center_point
            raise ValueError('type is %s, need to be upgraded'%inter_lines.geom_type)

        inter_line_length.append(inter_lines.length)

    # output the maximum length and angle
    max_line_length = max(inter_line_length)
    angle_max = angle_list[max_d_ele_index_list[inter_line_length.index(max_line_length)]]

    return max_line_length, angle_max, x0, y0


def cal_distance_along_slope(exp_polygon,medial_axis, radiuses, dem_path):
    '''
    calculate distance at the direction of maximum elevation difference (not on the slope)
    :param exp_polygon:
    :param medial_axis:
    :param radiuses:
    :param dem_path:
    :return:
    '''

    # sample the medial circles
    top_n_index = find_top_n_medial_circle_with_sampling(medial_axis, radiuses, sep_distance=20, n=10)

    img_obj = RSImageclass()
    img_obj.open(dem_path)
    dem_resolution = img_obj.GetXresolution()

    # for each meidal circle, try to calculate the distance at the maximum elevation difference direction
    dis_at_max_dem_diff_list = []
    angle_list = []
    center_point_list = []

    for n_index in top_n_index:
        dis_at_max_dem_diff, angle, x0, y0 = meidal_circles_segment(exp_polygon,medial_axis[n_index], radiuses[n_index],dem_path, dem_resolution)
        dis_at_max_dem_diff_list.append(dis_at_max_dem_diff)
        angle_list.append(angle)
        center_point_list.append((x0,y0))

    # choose the maximum one as output
    max_value = max(dis_at_max_dem_diff_list)
    max_index = dis_at_max_dem_diff_list.index(max_value)
    angle_at_max = angle_list[max_index]
    center_at_max = center_point_list[max_index]
    return max_value, angle_at_max, center_at_max

def cal_one_expand_area_dis(idx,exp_polygon, total_polygon_count):

    basic.outputlogMessage(
        'Calculating expanding distance of %dth (0 index) polygon, total: %d' % (idx, total_polygon_count))

    proc_id = multiprocessing.current_process().pid
    # print(proc_id)

    h_value = 0.3       # default h for calculating medial axis
    if exp_polygon.area < 1:
        # for a small polygon, it may failed to calculate its radiues, so get a approximation values
        basic.outputlogMessage('The polygon is very small (area < 1), use sqrt(area/pi) as its radius')
        radiuses = np.array([[math.sqrt(exp_polygon.area / math.pi)]])
    else:


        x_list, y_list = exp_polygon.exterior.coords.xy
        # xy = exp_polygon.exterior.coords
        vertices = [(x, y) for (x, y) in zip(x_list, y_list)]
        vertices = np.array(vertices)

        # interrupted by signal 11: SIGSEGV or segmentation fault may be avoid if change the h value
        medial_axis, radiuses, h_value = get_medial_axis_of_one_polygon(vertices, h=h_value, proc_id=proc_id)

    # to 1d
    radiuses_1d = [value for item in radiuses for value in item]
    # remove redundant ones, if apply this, the mean and median value may change
    radiuses_noRed = set(radiuses_1d)
    np_rad_nored = np.array(list(radiuses_noRed))
    min_medAxis_width = np.min(np_rad_nored)
    max_medAxis_width = np.max(np_rad_nored)
    mean_medAxis_width = np.mean(np_rad_nored)
    median_medAxis_width = np.median(np_rad_nored)  # np median will take the average of the middle two if necessary

    # poly_min_Ws.append(min_medAxis_width * 2)  # multiply by 2, then it is diameter
    # poly_max_Ws.append(max_medAxis_width * 2)
    # poly_mean_Ws.append(mean_medAxis_width * 2)
    # poly_median_Ws.append(median_medAxis_width * 2)

    return idx, min_medAxis_width * 2, max_medAxis_width * 2, mean_medAxis_width * 2, median_medAxis_width * 2, h_value


def cal_expand_area_distance(expand_shp, dem_path = None):
    '''
    calculate the distance of expanding areas along the upslope direction.
    The distance will save to expand_shp, backup it if necessary
    :param expand_shp: the shape file containing polygons which represent expanding areas of active thaw slumps
    :param dem_path: the dem path for calculating the slope distance along slope
    :return: True if successful
    '''

    # read polygons
    # read polygons as shapely objects
    expand_polygons = vector_gpd.read_polygons_gpd(expand_shp)
    if len(expand_polygons) < 1:
        raise ValueError('No polygons in %s' % expand_shp)

    # check projection
    if dem_path is not None:
        if get_projection_proj4(expand_shp) != get_projection_proj4(dem_path):
            raise ValueError('error, projection insistence between %s and %s' % (expand_shp, dem_path))

    poly_min_Ws = []     #min_medAxis_width
    poly_max_Ws = []     #max_medAxis_width
    poly_mean_Ws = []    #mean_medAxis_width
    poly_median_Ws = []  #median_medAxis_width
    h_value_list = []
    dis_slope_list = []      # distance along slope (direction of maximum elevation difference)
    dis_angle_list = []     #relative to x axis
    dis_l_x0_list = []      # the center point of line passes
    dis_l_y0_list = []


    # # parallel getting medial axis of each polygon, then calculate distance.
    # num_cores = multiprocessing.cpu_count()
    # print('number of thread %d' % num_cores)
    # theadPool = Pool(num_cores)  # multi processes
    #
    # parameters_list = [
    #     (idx, exp_polygon, len(expand_polygons)) for idx, exp_polygon in enumerate(expand_polygons)]
    # results = theadPool.starmap(cal_one_expand_area_dis, parameters_list)  # need python3
    # for result in results:
    #     # it still has the same order as expand_polygons
    #     print('get result of %dth polygon'%result[0])
    #     poly_min_Ws.append(result[1])    # min_medAxis_width*2
    #     poly_max_Ws.append(result[2])    # max_medAxis_width*2
    #     poly_mean_Ws.append(result[3])   # mean_medAxis_width*2
    #     poly_median_Ws.append(result[4]) # median_medAxis_width*2
    #     h_value_list.append(result[5]) # the h value for getting medial axis


    ################################################
    # go through each polygon, get its medial axis, then calculate distance.
    for idx, exp_polygon in enumerate(expand_polygons):

        basic.outputlogMessage('Calculating expanding distance of %dth (0 index) polygon, total: %d'%(idx,len(expand_polygons)))
        # if idx == 13:
        #     test = 1

        h_value = 0.3
        dis_slope = 0.0
        dis_direction = 0  # relative to x axis
        dis_line_p_x0 = 0.0
        dis_line_p_y0 = 0.0

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

            # medial_axis, radiuses = compute_polygon_medial_axis(vertices, h=h_value)
            # except Exception as e:  # can get all the exception, and the program will not exit
            #     basic.outputlogMessage('unknown error: ' + str(e))
            ####################################################################################

            # interrupted by signal 11: SIGSEGV or segmentation fault may be avoid if change the h value
            medial_axis, radiuses, h_value = get_medial_axis_of_one_polygon(vertices, h=0.3)

            if dem_path is not None:
                dis_slope, dis_direction, l_c_point = cal_distance_along_slope(exp_polygon, medial_axis, radiuses, dem_path=dem_path)
                dis_line_p_x0, dis_line_p_y0 = l_c_point

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
        h_value_list.append(h_value)
        dis_slope_list.append(dis_slope)
        dis_angle_list.append(dis_direction)
        dis_l_x0_list.append(dis_line_p_x0)
        dis_l_y0_list.append(dis_line_p_y0)

    #
        # break

    # save the distance to shapefile
    shp_obj = shape_opeation()
    shp_obj.add_one_field_records_to_shapefile(expand_shp, poly_min_Ws, 'e_min_dis')
    shp_obj.add_one_field_records_to_shapefile(expand_shp, poly_max_Ws, 'e_max_dis')
    shp_obj.add_one_field_records_to_shapefile(expand_shp, poly_mean_Ws, 'e_mean_dis')
    shp_obj.add_one_field_records_to_shapefile(expand_shp, poly_median_Ws, 'e_medi_dis')
    shp_obj.add_one_field_records_to_shapefile(expand_shp, h_value_list, 'e_medi_h')
    shp_obj.add_one_field_records_to_shapefile(expand_shp, dis_slope_list, 'e_dis_slop')
    shp_obj.add_one_field_records_to_shapefile(expand_shp, dis_slope_list, 'e_dis_slop')
    shp_obj.add_one_field_records_to_shapefile(expand_shp, dis_l_x0_list, 'e_dis_p_x0')
    shp_obj.add_one_field_records_to_shapefile(expand_shp, dis_l_y0_list, 'e_dis_p_y0')

    basic.outputlogMessage('Save expanding distance of all the polygons to %s'%expand_shp)

    return True

def getDis(point1, point2):
    dx = point1[0]-point2[0]
    dy = point1[1]-point2[1]
    return math.sqrt(dx*dx + dy*dy)

def find_top_n_medial_circle_with_sampling(medial_axis, radiuses, sep_distance=10, n=10):
    '''
    find N largest medial circle, each of them separately at least sep_distance
    :param medial_axis:
    :param radiuses:
    :param sep_distance:
    :param n:
    :return:
    '''

    # sort, from max to min
    radiuses_sorted = sorted(radiuses, reverse=True)    # each has two r, very close
    found_medial_axis = []
    found_index = []
    for sort_r in radiuses_sorted:

        index = radiuses.index(sort_r)  # the index in medial_axis
        (x1, y1), (x2, y2) = medial_axis[index]
        # check distance
        b_well_separated = True
        for m_axis in found_medial_axis:
            (x1_f, y1_f), (x2_f, y2_f) = m_axis
            if getDis((x1, y1),(x1_f, y1_f)) < sep_distance or getDis((x1, y1),(x2_f, y2_f)) < sep_distance or \
                getDis((x2, y2), (x1_f, y1_f)) < sep_distance or getDis((x2, y2), (x2_f, y2_f)) < sep_distance:
                b_well_separated = False

        if b_well_separated:
            found_medial_axis.append([(x1, y1), (x2, y2)])
            found_index.append(index)

        if len(found_medial_axis) >= n:
            break

    # top_N_radius =radiuses_sorted[:100]
    # top_n_index = [ radiuses.index(item) for item in top_N_radius ]

    print('intend to find %d, in fact, found %d' % (n, len(found_medial_axis)))

    return found_index

def main(options, args):

    # # a test of compute_polygon_medial_axis
    # import numpy as np
    # import matplotlib.pyplot as plt
    # polygon = np.loadtxt("out_polygon_vertices_38113.txt") #sys.argv[1], polygon_1.txt, polygon_2.txt
    # fig, ax = plt.subplots(figsize=(8, 8))
    # medial_axis, radiuses = compute_polygon_medial_axis(polygon, h=0.1)   # it seems that smaller h can output detailed medial axis.
    #
    # max_r = max(radiuses)
    # max_r_idx = radiuses.index(max_r)
    # print('max_r',max_r, 'max_r_idx', max_r_idx)
    #
    # top_n_index = find_top_n_medial_circle_with_sampling(medial_axis, radiuses, sep_distance=20, n=8)
    #
    # plot_polygon_medial_axis(polygon, medial_axis, circ_radius=radiuses, draw_circle_idx=top_n_index, ax=ax)
    # ax.axis('equal')
    # ax.set_title('Medial Axis')
    # plt.show()

    cal_expand_area_distance(args[0], dem_path=options.dem_path)

    pass



if __name__ == "__main__":
    usage = "usage: %prog [options]  change_polygon.shp "
    parser = OptionParser(usage=usage, version="1.0 2020-01-31")
    parser.description = 'Introduction: calculate the retreat rates of thaw slumps based on their expanding areas '

    parser.add_option("-p", "--para",
                      action="store", dest="para_file",
                      help="the parameters file")

    parser.add_option("-d", "--dem_path",
                      action="store", dest="dem_path",
                      help="the path for the digital elevation model (DEM)")

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