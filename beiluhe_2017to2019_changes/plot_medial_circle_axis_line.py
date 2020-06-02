#!/usr/bin/env python
# Filename: plot_medial_circle_axis_line 
"""
introduction: plot polygons (in a shapefile) and the corresponding medial circle as well as axis

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 02 June, 2020
"""

import os, sys
import numpy as np
import matplotlib.pyplot as plt
import math

import shapely
from shapely.geometry import LineString
from shapely.geometry import Point
from shapely.geometry import Polygon

import geopandas as gpd

sys.path.append(os.path.expanduser('~/codes/PycharmProjects/ChangeDet_DL/thawSlumpChangeDet'))
from cal_retreat_rate import find_top_n_medial_circle_with_sampling
# from cal_retreat_rate import plot_polygon_medial_axis_circle_line
from cal_retreat_rate import get_projection_proj4
from cal_retreat_rate import get_medial_axis_of_one_polygon
from cal_retreat_rate import cal_one_expand_area_dis
from cal_retreat_rate import cal_distance_along_slope
from cal_retreat_rate import cal_distance_along_expanding_line
from cal_retreat_rate import cal_distance_along_polygon_center
import basic_src.basic as basic
import basic_src.io_function as io_function

import vector_gpd
import rasterio

test_dir = os.path.expanduser('~/Data/Qinghai-Tibet/beiluhe/beiluhe_planet/polygon_based_ChangeDet/test_cal_retreat_dis')
dem_path = os.path.expanduser('~/Data/Qinghai-Tibet/beiluhe/DEM/srtm_30/beiluhe_srtm30_utm.tif')

expand_shp = os.path.join(test_dir,'polygons_for_test_retreat_dis_2017vs2018.shp')
old_shp = os.path.expanduser('~/Data/Qinghai-Tibet/beiluhe/thaw_slumps/train_polygons_for_planet_201707/blh_manu_RTS_utm_201707.shp')
expand_line = os.path.expanduser('~/Data/Qinghai-Tibet/beiluhe/thaw_slumps/rts_expanding_direction_2017to2019/rts_expanding_line_201707_vs_201807.shp')
# expand_shp = os.path.join(test_dir,'polygons_for_test_retreat_dis_2018vs2019.shp')
out_dir = os.path.join(test_dir,'figures_'+os.path.splitext(os.path.basename(expand_shp))[0])


io_function.mkdir(out_dir)


## copy and modified from ~/codes/PycharmProjects/yghlc_Computational-Geometry/HW/lib/polygon_delaunay_triangulation.py
def plot_polygon(vertices, ax=None):
    """ plot polygon """
    if not ax:
        fig, ax = plt.subplots(figsize=(8, 8))
    assert(vertices.shape[0] >= 3)
    vs = np.vstack((vertices, vertices[0:1, :]))
    # ax.plot(vs[:, 0], vs[:, 1], 'b-o', linewidth=2)
    ax.plot(vs[:, 0], vs[:, 1], 'k-', linewidth=2)

## copy and modified from ~/codes/PycharmProjects/yghlc_Computational-Geometry/HW/lib/polygon_medial_axis.py
def plot_polygon_medial_axis(vertices, medial_axis, circ_radius=None, draw_circle_idx = 0, ax=None):
    """ plot the polygon defined by vertices and its medial axis"""

    if isinstance(draw_circle_idx, list) is False:
        draw_circle_idx = [draw_circle_idx]

    if not ax:
        fig, ax = plt.subplots(figsize=(8, 8))
    for idx, ((x1, y1), (x2, y2)) in enumerate(medial_axis):
        ax.plot([x1, x2], [y1, y2], 'r--')

        # draw circle
        if circ_radius is not None and idx in draw_circle_idx:
            circle1 = plt.Circle((x1, y1), circ_radius[idx][0], color='deepskyblue',fill=False)
            # circle2 = plt.Circle((x2, y2), circ_radius[idx][1], color='green',fill=False)
            ax.add_artist(circle1)
            # ax.add_artist(circle2)

            # #only draw one circle and its center
            # circle1 = plt.Circle((x1, y1), circ_radius[idx][0], color='deepskyblue',fill=False)
            # ax.add_artist(circle1)
            # draw the center point
            ax.plot(x1,y1, marker='o', color='black', markersize=3)


    plot_polygon(vertices, ax=ax)


# copied and modified from cal_retreat_rate.py
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
        ax.plot(line_obj[0],line_obj[1],marker='o',color='black',markersize=8)

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
    # ax.set_title('Medial Axis')
    plt.axis('off')
    if save_path is None:
        plt.show()
    else:
        plt.savefig(save_path,dpi=200)
        basic.outputlogMessage('Save medial axis and circle to %s'%save_path)

def main():

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


    ##################################################################
    results = []
    h_value = 0.3  # default h for calculating medial axis
    proc_id = 100
    for idx, exp_polygon in enumerate(expand_polygons):
        res = cal_one_expand_area_dis(idx, exp_polygon, len(expand_polygons), dem_path, old_poly_list[idx],e_line_list[idx])
        print(res)
        results.append(res)

        x_list, y_list = exp_polygon.exterior.coords.xy
        # xy = exp_polygon.exterior.coords
        vertices = [(x, y) for (x, y) in zip(x_list, y_list)]
        vertices = np.array(vertices)

        # interrupted by signal 11: SIGSEGV or segmentation fault may be avoid if change the h value
        medial_axis, radiuses, h_value = get_medial_axis_of_one_polygon(vertices, h=h_value, proc_id=proc_id)

        save_path = os.path.join(out_dir,"medial_axis_circle_for_%d_polygon.jpg" % idx)
        top_n_index = find_top_n_medial_circle_with_sampling(medial_axis, radiuses, sep_distance=15, n=20)
        plot_polygon_medial_axis_circle_line(vertices,medial_axis,radiuses,top_n_index,save_path=save_path)

        old_poly = None
        # old_poly = old_poly_list[idx]

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
            dis_e_line = cal_distance_along_expanding_line(idx, exp_polygon,expand_line)


        # break

    # polygons




if __name__ == "__main__":
    main()