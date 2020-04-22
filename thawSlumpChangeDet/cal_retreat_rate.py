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
from shapely.geometry import Polygon

import rasterio

import geopandas as gpd

# parameter for sampling medial circles
global_sep_distance = 20
global_topSize_count = 3

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
    print('medial_axis_radiuses.shape:',medial_axis_radiuses.shape)
    medial_axis = []
    radiuses = []
    for row in medial_axis_radiuses:
        x1, y1, x2, y2, r1, r2 = row
        medial_axis.append(((x1,y1),(x2,y2)))
        radiuses.append((r1,r2))
    return medial_axis, radiuses, h

def meidal_circles_segment(exp_polygon,a_medial_axis, radius,dem_src, dem_res):

    (x1, y1), (x2, y2) = a_medial_axis  # (x1, y1) and (x2, y2) are close to each other
    r1, r2 = radius

    # use the one with larger radius
    x0, y0, r = x1, y1, r1
    if r2 > r1:
        x0, y0, r = x2, y2, r2

    # for (x0,y0), r in zip(a_medial_axis, radius):

    center_point = Point(x0,y0)
    # half length of the line segment for calculating elevation difference
    line_half_len_for_dem = r + dem_res # + 10 #max(dem_res/2.0, 10)

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
        # ele_s = RSImage.get_image_location_value(dem_path,xs,ys,'prj',1)
        # ele_e = RSImage.get_image_location_value(dem_path,xe,ye,'prj',1)

        ele_s,ele_e = [val for val in dem_src.sample([(xs,ys), (xe,ye)],1)]
        # for test
        # print(xs,ys,ele_s[0])
        # print(xe,ye,ele_e[0])


        diff_ele = abs(ele_s[0] - ele_e[0])
        # print(diff_ele)

        diff_ele_list.append(diff_ele)
        angle_list.append(angle)

    # find the maximum elevation difference (could have multiple values)
    max_diff_eles = max(diff_ele_list)
    max_d_ele_index_list =  [i for i, x in enumerate(diff_ele_list) if x == max_diff_eles]

    box = exp_polygon.bounds
    line_half_len_for_interset = max(abs(box[2]-box[0]), abs(box[3] - box[1]))/2.0
    inter_line_length = []
    inter_line_angle = []
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
        inter_line_angle.append(angle_list[index])

    # # output the maximum length and angle
    # max_line_length = max(inter_line_length)
    # angle_max = angle_list[max_d_ele_index_list[inter_line_length.index(max_line_length)]]
    #
    # return max_line_length, angle_max, x0, y0

    # output the median value
    inter_line_length_np = np.array(inter_line_length)
    # median_line_length = np.median(inter_line_length_np)      # if even, the median is interpolated by taking the average of the two middle values
    median_line_length = np.sort(inter_line_length_np)[len(inter_line_length_np)//2]
    angle_median = inter_line_angle[inter_line_length.index(median_line_length)]

    return median_line_length, angle_median, x0, y0

def meidal_circles_segment_across_center(exp_polygon,a_medial_axis, radius, old_polygon):

    (x1, y1), (x2, y2) = a_medial_axis  # (x1, y1) and (x2, y2) are close to each other
    r1, r2 = radius

    # use the one with larger radius
    x0, y0, r = x1, y1, r1
    if r2 > r1:
        x0, y0, r = x2, y2, r2

    center_point = Point(x0,y0)
    # Centroid (geometric center ) of the old polygon
    old_polygon_center = old_polygon.centroid
    old_c_x = old_polygon_center.x
    old_c_y = old_polygon_center.y

    # calculate angle (reference to x axis, range 0 - 180)
    rad = math.atan2((old_c_y - y0) , (old_c_x - x0)) # get value between -pi to pi
    # rad = math.atan((old_c_y - y0)/(old_c_x - x0))     # get value between -pi/2 to pi/2
    angle = math.degrees(rad) # + 90

    # construct a long line
    box = exp_polygon.bounds
    line_half_len_for_interset = max(abs(box[2]-box[0]), abs(box[3] - box[1]))/2.0
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
            # only one line will intersect with the center point
            if a_line.buffer(0.1).intersection(center_point).is_empty:
                continue
            else:
                inter_lines = a_line
                break
    else:
        # if there are multiple lines, need to find the one intersect with center_point
        raise ValueError('type is %s, need to be upgraded'%inter_lines.geom_type)

    # for test
    print('x0',x0, 'y0',y0, 'length',inter_lines.length,'rad', rad, 'angle', angle)

    return inter_lines.length, angle, x0, y0


def cal_distance_along_polygon_center(exp_polygon,medial_axis, radiuses,old_polygon):
    '''
    calculating the retreat distance along the direction from old polygon center and medial circle center
    :param exp_polygon: a expanding polygon
    :param medial_axis:
    :param radiuses:
    :param old_polygon: the corresponding center
    :return:
    '''

    #  return
    if old_polygon is None:
        basic.outputlogMessage('Warning, The old polygon is None, skip cal_distance_along_polygon_center')
        return 0.0, 0.0, (0.0,0.0)

    # sample the medial circles
    top_n_index = find_top_n_medial_circle_with_sampling(medial_axis, radiuses, sep_distance=global_sep_distance, n=global_topSize_count)

    # for each meidal circle, try to calculate the distance at the direction from center of old_polygon to the circle center
    dis_at_center_list = []
    angle_list = []
    center_point_list = []      # the circle center

    for n_index in top_n_index:
        dis_across_center, angle, x0, y0 = meidal_circles_segment_across_center(exp_polygon,medial_axis[n_index], radiuses[n_index],old_polygon)
        dis_at_center_list.append(dis_across_center)
        angle_list.append(angle)
        center_point_list.append((x0,y0))

    # choose the maximum one as output
    max_value = max(dis_at_center_list)  #np.median
    max_index = dis_at_center_list.index(max_value)
    angle_at_max = angle_list[max_index]
    center_at_max = center_point_list[max_index]
    return max_value, angle_at_max, center_at_max


def cal_distance_along_slope(exp_polygon,medial_axis, radiuses, dem_src):
    '''
    calculate distance at the direction of maximum elevation difference (not on the slope)
    :param exp_polygon:
    :param medial_axis:
    :param radiuses:
    :param dem_src: dem rasterio object
    :return:
    '''

    # sample the medial circles
    top_n_index = find_top_n_medial_circle_with_sampling(medial_axis, radiuses, sep_distance=global_sep_distance, n=global_topSize_count)


    dem_resolution, _ =  dem_src.res

    # for each meidal circle, try to calculate the distance at the maximum elevation difference direction
    dis_at_max_dem_diff_list = []
    angle_list = []
    center_point_list = []

    for n_index in top_n_index:
        dis_at_max_dem_diff, angle, x0, y0 = meidal_circles_segment(exp_polygon,medial_axis[n_index], radiuses[n_index],dem_src, dem_resolution)
        dis_at_max_dem_diff_list.append(dis_at_max_dem_diff)
        angle_list.append(angle)
        center_point_list.append((x0,y0))

    # choose the maximum one as output
    max_value = max(dis_at_max_dem_diff_list)  #np.median
    max_index = dis_at_max_dem_diff_list.index(max_value)
    angle_at_max = angle_list[max_index]
    center_at_max = center_point_list[max_index]
    return max_value, angle_at_max, center_at_max

def cal_distance_along_expanding_line(idx, exp_polygon,expanding_line):
    inter_lines = expanding_line.intersection(exp_polygon)

    if inter_lines.geom_type == 'LineString':
        return inter_lines.length
    elif inter_lines.geom_type == 'MultiLineString':
        # if there are multiple lines, need to find the one intersect with center_point
        raise ValueError('The line at location of %d expanding polygon cross multiple polygons '%idx)

    pass

def cal_one_expand_area_dis(idx,exp_polygon, total_polygon_count, dem_path, old_poly, expand_line):

    basic.outputlogMessage(
        'Calculating expanding distance of %dth (0 index) polygon, total: %d' % (idx, total_polygon_count))

    proc_id = multiprocessing.current_process().pid
    # print(proc_id)

    h_value = 0.3       # default h for calculating medial axis
    dis_slope = 0.0
    dis_direction = 0.0  # relative to x axis
    dis_line_p_x0 = 0.0
    dis_line_p_y0 = 0.0

    # distance along old polygon center to medial circle (center)
    dis_along_center = 0.0
    dis_c_angle = 0.0
    dis_c_line_x0 = 0.0
    dis_c_line_y0 = 0.0

    # distance along expanding line (manually draw)
    dis_e_line = 0.0

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

        if dem_path is not None:
            dem_src = rasterio.open(dem_path)
            dis_slope, dis_direction, l_c_point = cal_distance_along_slope(exp_polygon, medial_axis, radiuses, dem_src=dem_src)
            dis_line_p_x0, dis_line_p_y0 = l_c_point

            # for test, draw the figures of medial circles (remove this when run in parallel)
            # save_path = "medial_axis_circle_for_%d_polygon.jpg"%idx
            # top_n_index = find_top_n_medial_circle_with_sampling(medial_axis, radiuses, sep_distance=global_sep_distance, n=global_topSize_count)
            # line_obj = [dis_line_p_x0, dis_line_p_y0,dis_direction,dis_slope]
            # plot_polygon_medial_axis_circle_line(vertices,medial_axis, radiuses,top_n_index,line_obj=line_obj, save_path=save_path)

        if old_poly is not None:
            dis_along_center, dis_c_angle, c_point = cal_distance_along_polygon_center(exp_polygon, medial_axis, radiuses,old_poly)
            dis_c_line_x0, dis_c_line_y0 = c_point

            # for test, draw the figures of medial circles  (remove this when run in parallel)
            # save_path = "medial_axis_circle_old_poly_center_for_%d_polygon.jpg"%idx
            # top_n_index = find_top_n_medial_circle_with_sampling(medial_axis, radiuses, sep_distance=global_sep_distance, n=global_topSize_count)
            # line_obj = [dis_c_line_x0, dis_c_line_y0,dis_c_angle,dis_along_center]
            # plot_polygon_medial_axis_circle_line(vertices,medial_axis, radiuses,top_n_index,line_obj=line_obj, save_path=save_path)

        if expand_line is not None:
            dis_e_line  = cal_distance_along_expanding_line(idx, exp_polygon,expand_line)


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

    return idx, min_medAxis_width * 2, max_medAxis_width * 2, mean_medAxis_width * 2, median_medAxis_width * 2, \
           h_value, dis_slope, dis_direction,dis_line_p_x0, dis_line_p_y0, \
           dis_along_center, dis_c_angle, dis_c_line_x0, dis_c_line_y0, dis_e_line


def cal_expand_area_distance(expand_shp, expand_line=None, dem_path = None, old_shp= None):
    '''
    calculate the distance of expanding areas along the upslope direction.
    The distance will save to expand_shp, backup it if necessary
    :param expand_shp: the shape file containing polygons which represent expanding areas of active thaw slumps
    :param expand_line: lines indicating the expanding the direction
    :param dem_path: the dem path for calculating the slope distance along slope
    :param old_shp: the shape file storing the old polygons
    :return: True if successful
    '''

    # read polygons
    # read polygons as shapely objects
    expand_polygons = vector_gpd.read_polygons_gpd(expand_shp)
    if len(expand_polygons) < 1:
        raise ValueError('No polygons in %s' % expand_shp)

    # read old polygon list for each expanding polygons
    old_poly_list = [None]*len(expand_polygons)
    if old_shp is not None:
        gpd_shapefile = gpd.read_file(expand_shp)
        old_poly_idx_list = gpd_shapefile['old_index'].tolist()
        old_polygons =  vector_gpd.read_polygons_gpd(old_shp)
        old_poly_list = [ old_polygons[idx] if idx >=0 else None for idx in old_poly_idx_list ]

    # read expanding lines (from manual input), put them at the some order of expanding polygons
    e_line_list = [None]*len(expand_polygons)
    if expand_line is not None:
        # check they have the same projection
        if get_projection_proj4(expand_shp) != get_projection_proj4(expand_line):
            raise ValueError('error, projection insistence between %s and %s' % (expand_shp, expand_line))

        lines = vector_gpd.read_lines_gpd(expand_line)
        line_checked = [False]*len(lines)
        for idx, e_polygon in enumerate(expand_polygons):
            e_line = vector_gpd.find_one_line_intersect_Polygon(e_polygon,lines,line_checked)
            e_line_list[idx] = e_line

    # dem_src = None
    # check projection
    if dem_path is not None:
        if get_projection_proj4(expand_shp) != get_projection_proj4(dem_path):
            raise ValueError('error, projection insistence between %s and %s' % (expand_shp, dem_path))

        # dem_src =rasterio.open(dem_path)

    poly_min_Ws = []     #min_medAxis_width
    poly_max_Ws = []     #max_medAxis_width
    poly_mean_Ws = []    #mean_medAxis_width
    poly_median_Ws = []  #median_medAxis_width
    h_value_list = []

    # distance along the direction of maximum elevation difference
    dis_slope_list = []      # distance along slope (direction of maximum elevation difference)
    dis_angle_list = []     #relative to x axis
    dis_l_x0_list = []      # the center point of line passes
    dis_l_y0_list = []

    # distance along the direction from old polygon center to center of medial centers
    dis_center_list = []        # distance along the direction from old polygon to medial circle center
    dis_c_angle_list = []       #relative to x axis, for testing and drawing the line
    dis_c_x0_list = []          # the center (x) of the medal circle, for drawing the line
    dis_c_y0_list = []          # the center (y) of the medal circle, for drawing the line

    # distance along expanding lines (manually draw)
    dis_e_line_list = []

    #####################################################################
    # parallel getting medial axis of each polygon, then calculate distance.
    num_cores = multiprocessing.cpu_count()
    print('number of thread %d' % num_cores)
    theadPool = Pool(num_cores)  # multi processes

    parameters_list = [
        (idx, exp_polygon, len(expand_polygons), dem_path, old_poly_list[idx], e_line_list[idx]) for idx, exp_polygon in enumerate(expand_polygons)]
    results = theadPool.starmap(cal_one_expand_area_dis, parameters_list)  # need python3

    # ######################################################################
    # # another way to test non-parallel version
    # results = []
    # for idx, exp_polygon in enumerate(expand_polygons):
    #     res = cal_one_expand_area_dis(idx, exp_polygon, len(expand_polygons), dem_path, old_poly_list[idx],e_line_list[idx])
    #     results.append(res)
    # ######################################################################

    for result in results:
        # it still has the same order as expand_polygons
        print('get result of %dth polygon'%result[0])
        poly_min_Ws.append(result[1])    # min_medAxis_width*2
        poly_max_Ws.append(result[2])    # max_medAxis_width*2
        poly_mean_Ws.append(result[3])   # mean_medAxis_width*2
        poly_median_Ws.append(result[4]) # median_medAxis_width*2
        h_value_list.append(result[5]) # the h value for getting medial axis

        if dem_path is not None:
            dis_slope_list.append(result[6])    #dis_slope
            dis_angle_list.append(result[7])    #dis_direction
            dis_l_x0_list.append(result[8]) # dis_line_p_x0
            dis_l_y0_list.append(result[9]) #dis_line_p_y0

        if old_shp is not None:
            dis_center_list.append(result[10])
            dis_c_angle_list.append(result[11])
            dis_c_x0_list.append(result[12])
            dis_c_y0_list.append(result[13])

        if expand_line is not None:
            dis_e_line_list.append(result[14])

    # ################################################
    # # go through each polygon, get its medial axis, then calculate distance.
    # for idx, exp_polygon in enumerate(expand_polygons):
    #
    #     basic.outputlogMessage('Calculating expanding distance of %dth (0 index) polygon, total: %d'%(idx,len(expand_polygons)))
    #     # if idx == 13:
    #     #     test = 1
    #
    #     h_value = 0.3
    #     dis_slope = 0.0
    #     dis_direction = 0  # relative to x axis
    #     dis_line_p_x0 = 0.0
    #     dis_line_p_y0 = 0.0
    #
    #     if exp_polygon.area < 1:
    #         # for a small polygon, it may failed to calculate its radiues, so get a approximation values
    #         basic.outputlogMessage('The polygon is very small (area < 1), use sqrt(area/pi) as its radius')
    #         radiuses = np.array([[math.sqrt(exp_polygon.area/math.pi)]])
    #     else:
    #
    #         # for test
    #         # print(idx, exp_polygon)
    #         # print(exp_polygon)
    #         # if idx < 13 or idx==55:
    #         #     continue
    #         x_list, y_list = exp_polygon.exterior.coords.xy
    #         # xy = exp_polygon.exterior.coords
    #         vertices = [ (x,y) for (x,y) in zip(x_list,y_list)]
    #         vertices = np.array(vertices)
    #         # polygon_dis.append(idx*0.1)
    #
    #         ############################ This way to call compute_polygon_medial_axis is unstale, sometime, it has error of:
    #         ### Process finished with exit code 139 (interrupted by signal 11: SIGSEGV)
    #         # medial_axis_obj = get_medial_axis_class()
    #         # h is used to sample points on bundary low h value, to reduce the number of points
    #         # medial_axis, radiuses = compute_polygon_medial_axis(vertices, h=0.5)
    #         # medial_axis, radiuses = medial_axis_obj.ref_compute_polygon_medial_axis(vertices, h=0.5)
    #         # medial_axis_obj = None
    #         # try:
    #
    #         # medial_axis, radiuses = compute_polygon_medial_axis(vertices, h=h_value)
    #         # except Exception as e:  # can get all the exception, and the program will not exit
    #         #     basic.outputlogMessage('unknown error: ' + str(e))
    #         ####################################################################################
    #
    #         # interrupted by signal 11: SIGSEGV or segmentation fault may be avoid if change the h value
    #         medial_axis, radiuses, h_value = get_medial_axis_of_one_polygon(vertices, h=0.3)
    #
    #         if dem_path is not None:
    #             dis_slope, dis_direction, l_c_point = cal_distance_along_slope(exp_polygon, medial_axis, radiuses, dem_src=dem_src)
    #             dis_line_p_x0, dis_line_p_y0 = l_c_point
    #
    #         # # ## for test
    #         # top_n_index = find_top_n_medial_circle_with_sampling(medial_axis, radiuses, sep_distance=20, n=3)
    #         # line_obj = [dis_line_p_x0, dis_line_p_y0,dis_direction,dis_slope]
    #         # plot_polygon_medial_axis_circle_line(vertices,medial_axis, radiuses,top_n_index,line_obj=line_obj)
    #         # # break
    #
    #     # to 1d
    #     radiuses_1d = [value for item in radiuses for value in item]
    #     # remove redundant ones, if apply this, it not the mean and median value may change
    #     radiuses_noRed = set(radiuses_1d)
    #     np_rad_nored = np.array(list(radiuses_noRed))
    #     min_medAxis_width = np.min(np_rad_nored)
    #     max_medAxis_width = np.max(np_rad_nored)
    #     mean_medAxis_width = np.mean(np_rad_nored)
    #     median_medAxis_width = np.median(np_rad_nored)      # np median will take the average of the middle two if necessary
    #
    #     poly_min_Ws.append(min_medAxis_width*2) # multiply by 2, then it is diameter
    #     poly_max_Ws.append(max_medAxis_width*2)
    #     poly_mean_Ws.append(mean_medAxis_width*2)
    #     poly_median_Ws.append(median_medAxis_width*2)
    #     h_value_list.append(h_value)
    #     dis_slope_list.append(dis_slope)
    #     dis_angle_list.append(dis_direction)
    #     dis_l_x0_list.append(dis_line_p_x0)
    #     dis_l_y0_list.append(dis_line_p_y0)
    #
    # #
    #     # break

    # save the distance to shapefile
    shp_obj = shape_opeation()
    shp_obj.add_one_field_records_to_shapefile(expand_shp, poly_min_Ws, 'e_min_dis')
    shp_obj.add_one_field_records_to_shapefile(expand_shp, poly_max_Ws, 'e_max_dis')
    shp_obj.add_one_field_records_to_shapefile(expand_shp, poly_mean_Ws, 'e_mean_dis')
    shp_obj.add_one_field_records_to_shapefile(expand_shp, poly_median_Ws, 'e_medi_dis')
    shp_obj.add_one_field_records_to_shapefile(expand_shp, h_value_list, 'e_medi_h')

    if dem_path is not None:
        shp_obj.add_one_field_records_to_shapefile(expand_shp, dis_slope_list, 'e_dis_slop')
        shp_obj.add_one_field_records_to_shapefile(expand_shp, dis_angle_list, 'e_dis_angl')
        shp_obj.add_one_field_records_to_shapefile(expand_shp, dis_l_x0_list, 'e_dis_p_x0')
        shp_obj.add_one_field_records_to_shapefile(expand_shp, dis_l_y0_list, 'e_dis_p_y0')

        diff_e_poly_max_slope_list = [  dis - max_Ws  for dis, max_Ws  in zip(dis_slope_list, poly_max_Ws)]
        shp_obj.add_one_field_records_to_shapefile(expand_shp, diff_e_poly_max_slope_list, 'diff_dis')

    if old_shp is not None:

        shp_obj.add_one_field_records_to_shapefile(expand_shp, dis_center_list, 'c_dis_cen')
        shp_obj.add_one_field_records_to_shapefile(expand_shp, dis_c_angle_list, 'c_dis_angl')
        shp_obj.add_one_field_records_to_shapefile(expand_shp, dis_c_x0_list, 'c_dis_p_x0')
        shp_obj.add_one_field_records_to_shapefile(expand_shp, dis_c_y0_list, 'c_dis_p_y0')

        diff_e_poly_cent_dis_list = [  dis - max_Ws  for dis, max_Ws  in zip(dis_center_list, poly_max_Ws)]
        shp_obj.add_one_field_records_to_shapefile(expand_shp, diff_e_poly_cent_dis_list, 'c_diff_dis')

    if expand_line is not None:
        shp_obj.add_one_field_records_to_shapefile(expand_shp, dis_e_line_list, 'e_dis_line')

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

def plot_polygon_medial_axis_circle_line(polygon, medial_axis,radiuses,draw_circle_idx,line_obj=None, save_path=None):
    # line_obj: (center_x, center_y, angle, length)

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 8))

    # polygon, medial_axis, circ_radius=radiuses, draw_circle_idx=top_n_index, ax=ax

    plot_polygon_medial_axis(polygon, medial_axis, circ_radius=radiuses, draw_circle_idx=draw_circle_idx, ax=ax)

    # plot the line
    if line_obj is not None:
        poly_shapely = Polygon(polygon)

        print('The length of the line with center (%f, %f) is %f, and its angle (relative to X axis) is %f:'%
              (line_obj[0], line_obj[1],line_obj[3],line_obj[2]))

        # draw the center point
        ax.plot(line_obj[0],line_obj[1],marker='+',color='black',markersize=20)

        # construct the line
        rad_angle = math.radians(line_obj[2])
        dx = line_obj[3]*math.cos(rad_angle)
        dy = line_obj[3]*math.sin(rad_angle)
        xs = line_obj[0] + dx
        ys = line_obj[1] + dy
        xe = line_obj[0] - dx
        ye = line_obj[1] - dy
        line_shapely = LineString([(xs,ys),(xe,ye)])
        inter_line = line_shapely.intersection(poly_shapely)

        x_list = []
        y_list = []
        center_point = Point(line_obj[0], line_obj[1])

        if inter_line.geom_type == 'MultiLineString':
            lines = list(inter_line)
            for a_line in lines:
                if a_line.buffer(0.1).intersection(center_point).is_empty:
                    continue
                else:
                    inter_line = a_line

        for coord in inter_line.coords:
            print(coord)
            x_list.append(coord[0])
            y_list.append(coord[1])
        #
        line_plt = plt.Line2D(x_list,y_list, color='black')
        ax.add_line(line_plt)



    ax.axis('equal')
    ax.set_title('Medial Axis')
    if save_path is None:
        plt.show()
    else:
        plt.savefig(save_path,dpi=200)
        basic.outputlogMessage('Save medial axis and circle to %s'%save_path)

def main(options, args):

    # # # a test of compute_polygon_medial_axis
    # # import numpy as np
    # polygon = np.loadtxt("out_polygon_vertices_38113.txt") #sys.argv[1], polygon_1.txt, polygon_2.txt
    # medial_axis, radiuses = compute_polygon_medial_axis(polygon, h=0.1)   # it seems that smaller h can output detailed medial axis.
    # max_r = max(radiuses)
    # max_r_idx = radiuses.index(max_r)
    # print('max_r',max_r, 'max_r_idx', max_r_idx)
    #
    # top_n_index = find_top_n_medial_circle_with_sampling(medial_axis, radiuses, sep_distance=20, n=8)
    # plot_polygon_medial_axis_circle_line(polygon,medial_axis,radiuses,top_n_index)


    cal_expand_area_distance(args[0],expand_line=options.expanding_line_shp, dem_path=options.dem_path, old_shp=options.old_polygon_shp)

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

    parser.add_option("-o", "--old_polygon_shp",
                      action="store", dest="old_polygon_shp",
                      help="the path to the old polygon shapefile ")

    parser.add_option("-l", "--expanding_line_shp",
                      action="store", dest="expanding_line_shp",
                      help="the path to the shapefile storing lines indicating the ")


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