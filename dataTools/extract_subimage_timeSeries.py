#!/usr/bin/env python
# Filename: extract_subimage_timeSeries 
"""
introduction: extract time series sub-images, input:
(1) time series images, (2) time series shape file contain landform polygons, and
(3) change detection results (optional)

notes: landform polygons can contain change information.

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 07 July, 2020
"""

import sys,os
from optparse import OptionParser

sys.path.insert(0,os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import basic_src.io_function as io_function
import basic_src.basic as basic
import vector_gpd
import basic_src.map_projection as map_projection
import raster_io
import basic_src.timeTools as timeTools

sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/Landuse_DL'))
from datasets.get_subImages import get_sub_image

from datasets.get_subImages import get_projection_proj4
# from datasets.get_subImages import check_projection_rasters
from datasets.get_subImages import meters_to_degress_onEarth
from datasets.get_subImages import get_image_tile_bound_boxes

from get_planet_image_list import get_Planet_SR_image_list_overlap_a_polygon
from mosaic_images_crop_grid import convert_planet_to_rgb_images

# import thest two to make sure load GEOS dll before using shapely
import shapely
import shapely.geometry

import geopandas as gpd
import rasterio

import pandas as pd
import parameters

import numpy as np

import matplotlib
# must be before importing matplotlib.pyplot or pylab!
if os.name == 'posix' and "DISPLAY" not in os.environ:
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cbook as cbook
from matplotlib_scalebar.scalebar import ScaleBar
import matplotlib.patches as patches
import calendar

import math

sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/ChangeDet_DL/thawSlumpChangeDet'))
import polygons_change_analyze

time_str_list = []


def check_projection_rasters(image_path_list):
    '''
    check the rasters: have the same projection,  use rasterio to get projection
    :param image_path_list: a list containing all the images
    :return:
    '''

    if len(image_path_list) < 2:
        return True
    proj4 = raster_io.get_projection(image_path_list[0], format='proj4')# get_projection_proj4()
    total_count = len(image_path_list)
    for idx in range(1,len(image_path_list)):
        proj4_tmp = raster_io.get_projection(image_path_list[idx],format='proj4')
        if proj4_tmp != proj4:
            raise ValueError('error, %s have different projection with the first raster'%image_path_list[idx])
        print('%d/%d projection of %s is %s'%(idx+1, total_count,image_path_list[idx],proj4_tmp))
    return True

def get_union_polygons_at_the_same_loc(shp_list, out_dir='./', union_save_path = None):
    '''
    get the union of mapped polygon at the same location
    :param shp_list:
    :return:
    '''
    if union_save_path is None:
        union_save_path = 'union_of_%s.shp'%'_'.join([str(item) for item in range(len(shp_list))])
    union_save_path = os.path.join(out_dir, union_save_path)   # put to the same folder of first shapefile
    if os.path.isfile(union_save_path):
        basic.outputlogMessage('%s already exist, skip'%union_save_path)
        return vector_gpd.read_polygons_gpd(union_save_path)

    polygons_list_2d = []
    for idx, shp in enumerate(shp_list):
        basic.outputlogMessage('read polygons from %dth shape file'%idx)
        polygons = vector_gpd.read_polygons_gpd(shp)
        polygons_list_2d.append(polygons)

    # get union of polygons at the same location
    union_polygons, occurrence_list, occur_time_list = polygons_change_analyze.get_polygon_union_occurrence_same_loc(polygons_list_2d)

    # save the polygon changes
    union_id_list = [item+1 for item in range(len(union_polygons))]
    occur_time_str_list = []
    for idx_list in occur_time_list:
        time_str = '_'.join([str(item) for item in idx_list])
        occur_time_str_list.append(time_str)

    union_df = pd.DataFrame({'id': union_id_list,
                            'time_occur': occurrence_list,
                            'time_idx': occur_time_str_list,
                            'UnionPolygon': union_polygons
                            })
    wkt_string = map_projection.get_raster_or_vector_srs_info_wkt(shp_list[0])
    vector_gpd.save_polygons_to_files(union_df, 'UnionPolygon', wkt_string, union_save_path)
    basic.outputlogMessage('Save the union polygons to %s'%union_save_path)

    return union_polygons

def get_image_list_2d_planet(xlsx_list,planet_image_table_list, polygon, polygon_id, cloud_cover_thr):
    '''
    get image file path at different time that covers the polygon
    :param xlsx_list: xlsx_list
    :param planet_image_table_list: Table list of planet records
    :param polygon: polygon (latlon) in shapely format
    :param polygon_id: polygon id
    :return:
    '''
    # images in each table in plant_image_table_list have the similar similar acquisition Date
    time_count = len(planet_image_table_list)        # the count of time period
    image_list_2d = []

    total_count = 0

    for time in range(time_count):
        xlsx_path = xlsx_list[time]
        img_folder_this_time = os.path.dirname(xlsx_path)
        # print(img_folder_this_time)
        table = planet_image_table_list[time]
        # get geojson_list based on cloud cover, asset count
        sel_records = table.loc[(table['asset_count']>=3) & (table['cloud_cover']<=cloud_cover_thr) ]
        geojson_list = [item for item in  sel_records['geojson'].to_list() if isinstance(item,str) and len(item) > 1]
        # change relative path to absolute path
        if len(geojson_list) > 0 and os.path.isfile(geojson_list[0]) is False:
            geojson_list = [ os.path.join(img_folder_this_time,item)  for item in geojson_list ]

        # [print(item) for item in geojson_list]
        # print('Done')
        image_path_list, cloud_cover_list = get_Planet_SR_image_list_overlap_a_polygon(polygon, geojson_list, cloud_cover_thr)
        # [print(item) for item in image_path_list]
        image_list_2d.append(image_path_list)

        total_count += len(image_path_list)

    return image_list_2d, total_count

def get_image_list_2d(input_image_dir,image_folder_list, pattern_list):
    '''
    get image file path at different time.
    :param image_folder_list:
    :param pattern_list:
    :return:
    '''
    image_list_2d = []  # 2D list, for a specific time, it may have multi images

    if len(image_folder_list) != len(pattern_list):
        raise ValueError('The length of image folder list and pattern list is different')

    for image_folder, pattern in zip(image_folder_list, pattern_list):
        # get image tile list
        # image_tile_list = io_function.get_file_list_by_ext(options.image_ext, image_folder, bsub_folder=False)
        folder_path = os.path.join(input_image_dir,image_folder)
        image_tile_list = io_function.get_file_list_by_pattern(folder_path,pattern)
        if len(image_tile_list) < 1:
            raise IOError('error, failed to get image tiles in folder %s'%folder_path)

        check_projection_rasters(image_tile_list)   # it will raise errors if found problems
        image_list_2d.append(image_tile_list)

    return image_list_2d


def organize_change_info(txt_path):


    pass

def get_time_series_subImage_for_polygons(polygons, time_images_2d, save_dir, bufferSize, pre_name, dstnodata, brectangle=True, b_draw = False,
                                          time_info_list=None, des_str_list=None):
    '''
    extract time series sub-images at different polygon location,
    :param polygons:
    :param time_images_2d:
    :param save_dir:
    :param bufferSize:
    :param pre_name:
    :param dstnodata:
    :param brectangle:
    :return:
    '''

    if time_info_list is not None:
        time_str_list = time_info_list
    if des_str_list is None:
        des_str_list = [None]*len(time_info_list)

    img_tile_boxes_list = []
    time_count = len(time_images_2d)
    for idx in range(time_count):
        img_tile_boxes = get_image_tile_bound_boxes(time_images_2d[idx])
        img_tile_boxes_list.append(img_tile_boxes)

    if b_draw:
        plt_obj = plt.figure()

    for idx, c_polygon in enumerate(polygons):
        # output message
        basic.outputlogMessage('obtaining %dth time series sub-images'%idx)

        # get buffer area
        expansion_polygon = c_polygon.buffer(bufferSize)

        # create a folder
        poly_save_dir = os.path.join(save_dir, pre_name + '_poly_%d_timeSeries'%idx)
        io_function.mkdir(poly_save_dir)

        ref_sub_image_for_polygon = None
        for time in range(time_count):
            image_tile_list = time_images_2d[time]
            img_tile_boxes = img_tile_boxes_list[time]

            # get one sub-image based on the buffer areas
            subimg_shortName = pre_name+'_poly_%d_t_%d.tif'%(idx,time)
            subimg_saved_path = os.path.join(poly_save_dir, subimg_shortName)
            if dstnodata is None:
                dstnodata = raster_io.get_nodata(image_tile_list[0])
            if get_sub_image(idx,expansion_polygon,image_tile_list,img_tile_boxes, subimg_saved_path, dstnodata, brectangle) is False:
                basic.outputlogMessage('Warning, skip the %dth polygon'%idx)

            # draw time and scale bar on images (annotate)
            if b_draw:
                draw_annotate_for_a_image(plt_obj,subimg_saved_path, time_str=time_str_list[time],
                                          type_str=des_str_list[time], polygon=c_polygon)
                if ref_sub_image_for_polygon is None:
                    ref_sub_image_for_polygon = subimg_saved_path

        if b_draw:
            draw_a_polygon(plt_obj,poly_save_dir,pre_name+'_poly_%d'%idx,c_polygon, ref_image=ref_sub_image_for_polygon)
        # test
        # sys.exit(0)

def get_time_str_list(image_folder_list):
    global time_str_list
    for folder_str in image_folder_list:
        year = folder_str[:4]
        month = folder_str[4:6]
        month_name = calendar.month_name[int(month)]
        time_str_list.append(year + ' ' +month_name)

def get_time_info_from_filename(image_path):
    filename = os.path.basename(image_path)
    return timeTools.date2str( timeTools.get_yeardate_yyyymmdd(filename) )

def draw_a_polygon(fig_obj, save_folder, pre_name, polygon,ref_image=None):
    if ref_image is not None:
        box = raster_io.get_image_bound_box(ref_image)
        img_extent = vector_gpd.convert_image_bound_to_shapely_polygon(box)
        p = gpd.GeoSeries([polygon,img_extent])
    else:
        p = gpd.GeoSeries(polygon)

    # frame = p.plot()
    frame = p.boundary.plot()   # only plot boundary, no fill
    frame.axes.get_xaxis().set_visible(False)
    frame.axes.get_yaxis().set_visible(False)

    save_fig = os.path.join(save_folder, pre_name + '_polygon.png')
    plt.savefig(save_fig, bbox_inches="tight")
    plt.close('all')
    # plt.show()
    return True

def get_rectangle_of_polygon_on_image(polygon_bounds,transform):
    # input the transform from raster io and  polygon_bounds: (minx, miny, maxx, maxy)
    # return xy : (float, float) The bottom and left rectangle coordinates
    #  and width, height
    xres = transform[0]
    x0 = transform[2]
    yres = transform[4]
    y0 = transform[5]

    x_left = math.floor((polygon_bounds[0] - x0)/xres)  # smaller value
    y_bottom = math.ceil((polygon_bounds[3] - y0)/yres) # larger value

    width = math.ceil((polygon_bounds[2] - polygon_bounds[0])/xres)
    heitht = math.ceil((polygon_bounds[1] - polygon_bounds[3])/yres)    # because yres is negative, so miny - maxy
    # print(x_left, y_bottom,width,heitht)

    return x_left, y_bottom,width,heitht


def draw_annotate_for_a_image(fig_obj, tif_image, time_str='0', type_str=None, polygon=None):
    # type_str: sensor, source of data, etc.


    with rasterio.open(tif_image) as img_obj:
        res = img_obj.res   # resolution
        width = img_obj.width
        height = img_obj.height
        indexes = img_obj.indexes

        # image = img_obj.read(indexes) #  plt.imread(tif_image)
        # image = np.transpose(image,(1,2,0))
        # print(image.shape)
        image = plt.imread(tif_image)
        # print(image_2.shape)
        plt.imshow(image)
        scalebar = ScaleBar(res[0])  # 1 pixel = 0.2 meter

        frame = plt.gca()
        frame.add_artist(scalebar)

        plt.text(10, height - 5, time_str, ha="left", size=14, color='white')
        if type_str is not None:
            plt.text(10, 5, type_str, ha="left", va='top', size=14, color='white')

        # draw a rectangle to mark the thaw slump
        if polygon is not None:
            # Create a Rectangle patch
            x_left, y_bottom,width,heitht = get_rectangle_of_polygon_on_image(polygon.bounds, img_obj.transform)
            rect = patches.Rectangle((x_left, y_bottom), width, heitht, linewidth=1, edgecolor='r', facecolor='none')
            # Add the patch to the Axes
            frame.add_patch(rect)

        frame.axes.get_xaxis().set_visible(False)
        frame.axes.get_yaxis().set_visible(False)

        save_fig = os.path.splitext(tif_image)[0] + '_draw.png'
        plt.savefig(save_fig, bbox_inches="tight")
        # plt.show()

        plt.clf()

    pass

def extract_timeSeries_from_mosaic_multi_polygons(para_file,txt_mosaic_polygons,bufferSize,out_dir,dstnodata,b_draw_scalebar_time,b_rectangle):

    input_image_dir = parameters.get_string_parameters(para_file, 'input_image_dir')
    input_image_dir = io_function.get_file_path_new_home_folder(input_image_dir)

    poly_shp_list = []
    image_folder_list = []
    image_pattern_list = []
    with open(txt_mosaic_polygons,'r') as f_obj:
        lines = [item.strip() for item in f_obj.readlines()]

        for idx in range(len(lines)):
            line = lines[idx]
            folder, pattern, polygon_shp = line.split(':')
            polygon_shp = io_function.get_file_path_new_home_folder(polygon_shp)
            poly_shp_list.append(polygon_shp)
            image_folder_list.append(folder)
            image_pattern_list.append(pattern)

    if len(poly_shp_list) < 1:
        raise IOError('No shape file in the list')

    if len(poly_shp_list) != len(image_folder_list):
        raise ValueError('The number of shape file and time image is different')

    get_time_str_list(image_folder_list)

    # 2D list, for a specific time, it may have multi images.
    image_list_2d = get_image_list_2d(input_image_dir, image_folder_list, image_pattern_list)

    # need to check: the shape file and raster should have the same projection.
    for polygons_shp, image_tile_list in zip(poly_shp_list, image_list_2d):
        if get_projection_proj4(polygons_shp) != get_projection_proj4(image_tile_list[0]):
            raise ValueError('error, the input raster (e.g., %s) and vector (%s) files don\'t have the same projection' % (image_tile_list[0], polygons_shp))

    # check these are EPSG:4326 projection
    if get_projection_proj4(poly_shp_list[0]).strip() == '+proj=longlat +datum=WGS84 +no_defs':
        bufferSize = meters_to_degress_onEarth(bufferSize)


    # get get union of polygons at the same location
    union_polygons = get_union_polygons_at_the_same_loc(poly_shp_list)

    ###################################################################

    pre_name = parameters.get_string_parameters(para_file, 'pre_name')

    # get_sub_images_and_labels(t_polygons_shp, t_polygons_shp_all, bufferSize, image_tile_list,
    #                           saved_dir, pre_name, dstnodata, brectangle=options.rectangle)

    # extract time-series sub-images
    # get_time_series_subImage_for_polygons(polygons, time_images_2d, save_dir, bufferSize, pre_name, dstnodata,
    #                                       brectangle=True):
    get_time_series_subImage_for_polygons(union_polygons,image_list_2d,out_dir,bufferSize, pre_name,
                                          dstnodata, brectangle=b_rectangle, b_draw=b_draw_scalebar_time)

def extract_timeSeries_from_planet_rgb_images(planet_images_dir_or_xlsx_list, cloud_cover_thr, para_file, txt_polygons, bufferSize,out_dir,dstnodata,b_draw_scalebar_time,b_rectangle):

    # get xlsx files which cotaining plaent scenes information
    # each xlsx contain images in the same period
    if os.path.isdir(planet_images_dir_or_xlsx_list):
        xlsx_list = io_function.get_file_list_by_ext('.xlsx',planet_images_dir_or_xlsx_list,bsub_folder=False)
        if len(xlsx_list) < 1:
            raise IOError('no xlsx files in %s, please run get_scene_list_xlsx.sh to generate them'%planet_images_dir_or_xlsx_list)
        # [ print(item) for item in xlsx_list]
        # sort, from oldest to newest
        xlsx_list = sorted(xlsx_list)
    else:
        with open(planet_images_dir_or_xlsx_list, 'r') as f_obj:
            lines = [item.strip() for item in f_obj.readlines()]
            xlsx_list = [io_function.get_file_path_new_home_folder(line) for line in lines]

    # read multi-temporal planet image records
    plant_image_table_list = []
    for idx, xlsx in enumerate(xlsx_list):
        basic.outputlogMessage('%d reading %s'%(idx, xlsx))
        table_pd = pd.read_excel(xlsx)
        plant_image_table_list.append(table_pd)

    time_count = len(xlsx_list)

    poly_shp_list = []
    with open(txt_polygons,'r') as f_obj:
        lines = [item.strip() for item in f_obj.readlines()]
        for idx in range(len(lines)):
            line = lines[idx]
            if len(line) < 1:
                continue
            polygon_shp = io_function.get_file_path_new_home_folder(line)
            poly_shp_list.append(polygon_shp)

    if len(poly_shp_list) < 1:
        raise IOError('No shape file in the list')

    if len(poly_shp_list) > 1:
        # get get union of polygons at the same location
        # basic.outputlogMessage('warning, multiple shapefiles are available, get unions of them at the same location')
        # union_polygons = get_union_polygons_at_the_same_loc(poly_shp_list)
        raise IOError('Only support one shapefile')
    # else:
        # union_polygons = vector_gpd.read_polygons_gpd(poly_shp_list[0])

    poly_shp_path = poly_shp_list[0]

    # check these are EPSG:4326 projection
    shp_prj = get_projection_proj4(poly_shp_path).strip()
    if shp_prj == '+proj=longlat +datum=WGS84 +no_defs':
        bufferSize = meters_to_degress_onEarth(bufferSize)

    polygons_latlon = vector_gpd.read_shape_gpd_to_NewPrj(poly_shp_path,'EPSG:4326')
    if len(polygons_latlon) < 1:
        raise ValueError('No polygons in %s'%poly_shp_path)
    else:
        basic.outputlogMessage('read %d polygons from %s'%(len(polygons_latlon),poly_shp_path ))
    polygon_ids = vector_gpd.read_attribute_values_list(poly_shp_path,'id')
    if polygon_ids is None:
        polygon_ids = [ id + 1 for id in range(len(polygons_latlon))]
    if None in polygon_ids:
        basic.outputlogMessage('Warning, None in the id attributes. The entire id attributes will be ignored')
        polygon_ids = [id + 1 for id in range(len(polygons_latlon))]

    pre_name = parameters.get_string_parameters(para_file, 'pre_name')


    if b_draw_scalebar_time:
        plt_obj = plt.figure()

    sr_min = parameters.get_string_parameters_None_if_absence(para_file,'sr_min')
    if sr_min is not None:
        sr_min = float(sr_min)
    else:
        sr_min = 0
    sr_max = float(parameters.get_string_parameters_None_if_absence(para_file,'sr_max'))
    if sr_max is not None:
        sr_max = float(sr_max)
    else:
        sr_max = 3000
    b_sharpen = parameters.get_bool_parameters_None_if_absence(para_file,'b_sharpen')
    if b_sharpen is None:
        b_sharpen = True

    for idx, (id, polygon_latlon) in enumerate(zip(polygon_ids, polygons_latlon)):
        basic.outputlogMessage('obtaining %dth time series sub-images (polygon id: %d)' % (idx, id))
        # get image_list_2d, # 2D list, for a specific time, it may have multi images.
        image_list_2d_a_polygon, img_count = get_image_list_2d_planet(xlsx_list,plant_image_table_list,polygon_latlon,id,cloud_cover_thr)

        if img_count < 1:
            basic.outputlogMessage('warning, no images found')
            continue

        # convert to RGB images
        image_list_2d_a_polygon_rgb = []
        for image_list in image_list_2d_a_polygon:
            rgb_list = []
            for img in image_list:
                rgb_img = convert_planet_to_rgb_images(img,sr_min=sr_min, sr_max=sr_max,sharpen=b_sharpen)
                rgb_list.append(rgb_img)
            image_list_2d_a_polygon_rgb.append(rgb_list)
        image_list_2d_a_polygon = image_list_2d_a_polygon_rgb

        img_tile_boxes_list = []
        time_count = len(image_list_2d_a_polygon)
        for time in range(time_count):
            img_tile_boxes = get_image_tile_bound_boxes(image_list_2d_a_polygon[time])
            img_tile_boxes_list.append(img_tile_boxes)

        # get sub_images, but need to have the same projection of images, different images may have different projection
        # especially for the large area,
        # TODO: reproject them if some of then have different projection
        raster_prj = None
        for image_path_list in image_list_2d_a_polygon:
            check_projection_rasters(image_path_list)  # it will raise errors if found problems
            if raster_prj is None and len(image_path_list) >0:
                raster_prj = get_projection_proj4(image_path_list[0]).strip()
        if shp_prj != raster_prj:
            polygons_tmp = vector_gpd.read_shape_gpd_to_NewPrj(poly_shp_path, raster_prj)
        else:
            polygons_tmp = vector_gpd.read_polygons_gpd(poly_shp_path)

        c_polygon = polygons_tmp[idx]

        # get buffer area
        expansion_polygon = c_polygon.buffer(bufferSize)

        # create a folder
        poly_save_dir = os.path.join(out_dir, pre_name + '_poly_%d_timeSeries'%id)
        io_function.mkdir(poly_save_dir)

        for time in range(time_count):
            image_tile_list = image_list_2d_a_polygon[time]
            if len(image_tile_list) < 1:
                continue
            img_tile_boxes = img_tile_boxes_list[time]

            # get one sub-image based on the buffer areas
            subimg_shortName = pre_name+'_poly_%d_t_%d.tif'%(id,time)
            subimg_saved_path = os.path.join(poly_save_dir, subimg_shortName)
            if get_sub_image(id,expansion_polygon,image_tile_list,img_tile_boxes, subimg_saved_path, dstnodata, b_rectangle) is False:
                basic.outputlogMessage('Warning, skip the polygon (id: %d) at %d time period'%(id,time))
                continue

            planet_base_name = os.path.basename(image_tile_list[0])
            acquired_date_str = planet_base_name[:4] + '-' +planet_base_name[4:6] + '-' + planet_base_name[6:8]
            # draw time and scale bar on images (annotate)
            if b_draw_scalebar_time:
                draw_annotate_for_a_image(plt_obj, subimg_saved_path, time_str=acquired_date_str, polygon=c_polygon)

    return True

def extract_timeSeries_from_shp(para_file, polygon_shp,bufferSize,out_dir,dstnodata,b_draw_scalebar_time,b_rectangle):

    # input_image_dir = parameters.get_directory(para_file, 'input_image_dir')
    # inf_image_or_pattern = parameters.get_string_parameters(para_file, 'inf_image_or_pattern')
    pre_name = parameters.get_string_parameters(para_file, 'pre_name')

    input_image_dir_Pattern_Description = parameters.get_string_parameters(para_file, 'input_image_dir_Pattern_Description')
    image_folder_list = []
    image_pattern_list = []
    image_desription_list = []
    with open(input_image_dir_Pattern_Description,'r') as f_obj:
        lines = [ ll.strip() for ll in f_obj.readlines()]
        for line in lines:
            folder, pattern, des = line.split(':')
            image_folder_list.append(os.path.expanduser(folder))
            image_pattern_list.append(pattern)
            image_desription_list.append(des)

    # 2D list, for a specific time, it may have multi images.
    image_list_2d = get_image_list_2d('', image_folder_list, image_pattern_list) # the folder is absolute, set input_image_dir as ""

    b_group_image_by_date = parameters.get_bool_parameters_None_if_absence(para_file,'b_group_image_by_date')
    if b_group_image_by_date is True:
        if len(image_list_2d) != 1:
            raise ValueError('try to group images by dates, by there are multiple image folders')
        img_groups = timeTools.group_files_yearmonthDay(image_list_2d[0],diff_days=0)
        image_list_2d = []
        for key in img_groups.keys():
            image_list_2d.append(img_groups[key])

    # get image list
    time_info_list = [get_time_info_from_filename(item[0]) for item in image_list_2d ]

    # need to check: the shape file and raster should have the same projection.
    poly_shp_prj = map_projection.get_raster_or_vector_srs_info_proj4(polygon_shp)
    for image_tile_list in image_list_2d:
        if poly_shp_prj != get_projection_proj4(image_tile_list[0]):
            raise ValueError('error, the input raster (e.g., %s) and vector (%s) files don\'t have the same projection' % (image_tile_list[0], polygon_shp))

    # read polygons
    polygons = vector_gpd.read_polygons_gpd(polygon_shp)
    if len(polygons) < 1:
        raise ValueError('No polygons in %s'% polygon_shp)


    get_time_series_subImage_for_polygons(polygons,image_list_2d,out_dir,bufferSize, pre_name,dstnodata, brectangle=b_rectangle,
                                          b_draw=b_draw_scalebar_time, time_info_list=time_info_list,des_str_list=image_desription_list)


    return True

def main(options, args):

    out_dir = options.out_dir
    if out_dir is None: out_dir = './'

    b_draw_scalebar_time = True

    para_file = options.para_file

    dstnodata = parameters.get_digit_parameters_None_if_absence(para_file, 'dst_nodata','int')  # None, it read from images
    bufferSize = parameters.get_digit_parameters (para_file, 'buffer_size','init')

    rectangle_ext = parameters.get_string_parameters(para_file, 'b_use_rectangle')
    if 'rectangle' in rectangle_ext:
        b_rectangle = True
    else:
        b_rectangle = False

    # if the input a shapefiles, then get time series sub-images for each polygons directly
    if args[0].endswith('.shp'):
        extract_timeSeries_from_shp(para_file, args[0], bufferSize, out_dir, dstnodata, b_draw_scalebar_time,
                                    b_rectangle)
        return True


    planet_images_dir_or_txt =  options.planet_images_dir_or_xlsxTXT

    if planet_images_dir_or_txt is not None:
        txt_polygons = args[0]

        cloud_cover_thr = options.cloud_cover  # 0.3
        cloud_cover_thr = cloud_cover_thr * 100  # in xml, it is percentage
        extract_timeSeries_from_planet_rgb_images(planet_images_dir_or_txt, cloud_cover_thr, para_file, txt_polygons,bufferSize, out_dir, dstnodata,
                                                  b_draw_scalebar_time, b_rectangle)
    else:
        txt_mosaic_polygons = args[0]
        extract_timeSeries_from_mosaic_multi_polygons(para_file,txt_mosaic_polygons,bufferSize,out_dir,dstnodata,b_draw_scalebar_time,b_rectangle)


    pass


if __name__ == "__main__":
    usage = "usage: %prog [options] polygon_image_list.txt or polygons.shp "
    parser = OptionParser(usage=usage, version="1.0 2020-7-7")
    parser.description = 'Introduction: get sub Images (time series) from multi-temporal images. polygons_shp may contain change information ' \
                         'The images and shape file should have the same projection.'

    parser.add_option("-e", "--image_ext",
                      action="store", dest="image_ext",default = '*.tif',
                      help="the image pattern of the image file")
    parser.add_option("-o", "--out_dir",
                      action="store", dest="out_dir", default = './',
                      help="the folder path for saving output files")

    parser.add_option("-i", "--planet_images_dir_or_xlsxTXT",
                      action="store", dest="planet_images_dir_or_xlsxTXT",
                      help="the folder containing Planet original images, if this is set, "
                           "it will extract the timeSeries from the original images")
    parser.add_option("-c", "--cloud_cover",
                      action="store", dest="cloud_cover", type=float,default=0.3,
                      help="the could cover threshold, only accept images with cloud cover less than the threshold")

    parser.add_option("-p", "--para_file",
                      action="store", dest="para_file",
                      help="the parameters file")


    (options, args) = parser.parse_args()
    if len(sys.argv) < 2 or len(args) < 1:
        parser.print_help()
        sys.exit(2)

    if options.para_file is None:
        basic.outputlogMessage('error, parameter file is required')
        sys.exit(2)

    main(options, args)