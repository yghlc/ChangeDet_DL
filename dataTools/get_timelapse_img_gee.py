#!/usr/bin/env python
# Filename: get_timelapse_img_gee 
"""
introduction: get time-lapse images using Google Earth Engine (GEE)



authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 08 December, 2019
"""

import sys,os
from optparse import OptionParser
from datetime import datetime


# path for DeeplabforRS
sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS/'))
import basic_src.basic as basic
import basic_src.io_function as io_function

import vector_gpd
from shapely.geometry import mapping        # transform to GeJSON format

import math

# input earth engine, used: ~/programs/anaconda3/envs/ee/bin/python, or change to ee by "source activate ee"
# need shapely, geopandas, gdal
import ee

# re-project
from pyproj import Proj, transform

shp_polygon_projection = None

def get_projection_proj4(geo_file):
    import basic_src.map_projection as map_projection
    return map_projection.get_raster_or_vector_srs_info_proj4(geo_file)

def meters_to_degress_onEarth(distance):
    return (distance/6371000.0)*180.0/math.pi

# quick test
def environment_test():
    # https://www.earthdatascience.org/tutorials/intro-google-earth-engine-python-api/
    # ee.Initialize()       # initialize in previous place
    image = ee.Image('srtm90_v4')
    print(image.getInfo())

def test_download():
    from pyproj import Proj, transform
    image = ee.Image(
        'LANDSAT/LE07/C01/T1/LE07_149035_20010930')  # change the name of this image if testing on another image is required
    projI = image.select(
        'B1').projection().getInfo()  # Exporting the whole image takes time, therefore, roughly select the center region of the image
    crs = projI['crs']
    outProj = Proj(init='epsg:4326')
    inProj = Proj(init=crs)
    kk = projI['transform']
    print(projI)
    lon1, lat1 = transform(inProj, outProj, kk[2] + (2000 * 30), kk[5] - (2000 * 30))
    lon2, lat2 = transform(inProj, outProj, kk[2] + (5000 * 30),
                           kk[5] - (5000 * 30))  # change these coordinates to increase or decrease image size

    bounds = [lon1, lat2, lon2, lat1]
    print(bounds, lon1, lat1)

    # imageL7=imageL7.select(['B1','B2','B3','B4','B5','B6_VCID_2','B7','B8'])
    imageL7 = image.select(['B1', 'B2', 'B3', 'B4', 'B5', 'B6_VCID_2', 'B7', 'B8'])  # bug fix -Lingcao
    geometry = ([lon1, lat1], [lon1, lat2], [lon2, lat2], [lon2, lat1])
    config = {
        'description': 'Landsat07image',
        'region': geometry,
        'scale': 15,  # the image is exported with 15m resolution
        'fileFormat': 'GeoTIFF'
    }
    #        'maxPixels': 1e12

    exp = ee.batch.Export.image.toDrive(imageL7, **config);

    exp.start()  # It takes around 5-10 minutes for 6000 * 6000 * 8 image to be exported
    print(exp.status())
    print(ee.batch.Task.list())
    import time
    while exp.active():
        print('Transferring Data to Drive..................')
        time.sleep(30)
    print('Done with the Export to the Drive')

def gee_download_time_lapse_images(start_date, end_date, cloud_cover_thr, img_type, polygon_shapely, polygon_idx, save_dir, buffer_size):
    '''
    python time lapse image using google earth engine
    :param start_date: start date, e.g., 2019-12-31
    :param end_date: e.g., 2019-12-31
    :param cloud_cover_thr: e.g., 0.3
    :param img_type: e.g., 'LANDSAT/LC08/C01/T1' or 'COPERNICUS/S2 or COPERNICUS/S2_SR'
    :param polygon_bound: the extent
    :param polygon_idx: the index of the polygon in the original folder
    :param buffer_size: buffer_size
    :return:
    '''

    # point = ee.Geometry.Point(-122.262, 37.8719)
    start = ee.Date(start_date)  # '%Y-%m-%d'
    finish = ee.Date(end_date)

    # get polygon bounding box (use the envelope)
    polygon_env = polygon_shapely.envelope
    x, y = polygon_env.exterior.coords.xy
    polygon_bound = ee.Geometry.Polygon([[x[0],y[0]],
                                         [x[1], y[1]],
                                         [x[2], y[2]],
                                         [x[3], y[3]]])

    filtercollection = ee.ImageCollection(img_type). \
        filterBounds(polygon_bound). \
        filterDate(start, finish). \
        filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_cover_thr*100)). \
        sort('CLOUD_COVER', True)
    # print(filtercollection)                 # print serialized request instructions
    print(filtercollection.getInfo())       # print object information

    select_image = ee.Image(filtercollection.first()).select(['B4','B3','B2'])
    print(select_image.getInfo())

    # polygon_idx
    export_dir = 'gee_saved' # os.path.join(save_dir,'sub_images_of_%d_polygon'%polygon_idx)

    projI = select_image.select('B4').projection().getInfo()  # Exporting the whole image takes time, therefore, roughly select the center region of the image
    img_crs = projI['crs']

    expansion_polygon = polygon_shapely.buffer(buffer_size)
    # re-projection if necessary
    img_projection = img_crs
    if img_projection != 'epsg:4326':
        from functools import partial
        import pyproj
        from shapely.ops import transform

        project = partial(
            pyproj.transform,
            pyproj.Proj(shp_polygon_projection),  # source coordinate system
            pyproj.Proj(img_projection))  # destination coordinate system

        expansion_polygon = transform(project, expansion_polygon)  # apply projection
        # polygon_shapely = transform(project, polygon_shapely)

    # export to google drive

    # expansion_polygon_json = mapping(expansion_polygon)
    x, y = expansion_polygon.envelope.exterior.coords.xy
    polygon_crop = ee.Geometry.Polygon([[x[0], y[0]],
                                         [x[1], y[1]],
                                         [x[2], y[2]],
                                         [x[3], y[3]]])
    print(polygon_crop.getInfo()['coordinates'])

    # config = {
    #     'description': 's2_test_image',
    #
    #     'region': polygon_crop.getInfo()['coordinates'],
    #     'scale': 10,  # the image is exported with 15m resolution
    #     'fileFormat': 'GeoTIFF',
    #     'maxPixels': 1e12
    # }
    #
    # exp = ee.batch.Export.image.toDrive(select_image, **config)

    # fileNamePrefix='myFilePrefix',
    # crs=myCRS
    # region = polygon_crop.getInfo()['coordinates'],
    #  folder=export_dir,
    task = ee.batch.Export.image.toDrive(image=select_image,
                                         description='s2_image_test_3',
                                         scale=10)

    task.start()
    print(task.status())
    print(ee.batch.Task.list())
    import time
    while task.active():
        print('Transferring Data to Drive..................')
        time.sleep(30)
    print('Done with the Export to the Drive')



    return True



def main(options, args):

    polygons_shp = args[0]
    time_lapse_save_folder = args[1]  # folder for saving downloaded images

    # check training polygons
    assert io_function.is_file_exist(polygons_shp)
    os.system('mkdir -p ' + time_lapse_save_folder)

    # initialize earth engine environment
    ee.Initialize()
    # environment_test()
    # test_download()

    # # check these are EPSG:4326 projection
    global shp_polygon_projection
    shp_polygon_projection = get_projection_proj4(polygons_shp).strip()
    if shp_polygon_projection == '+proj=longlat +datum=WGS84 +no_defs':
        crop_buffer = meters_to_degress_onEarth(options.buffer_size)
    else:
        crop_buffer = options.buffer_size


    # read polygons, not json format, but shapely format
    polygons = vector_gpd.read_polygons_json(polygons_shp, no_json=True)

    for idx, geom in enumerate(polygons):

        basic.outputlogMessage('downloading and cropping images for %dth polygon, total: %d polygons'%
                               (idx+1, len(polygons)))

        gee_download_time_lapse_images(options.start_date, options.end_date, options.cloud_cover,
                                       options.image_type, geom, idx, time_lapse_save_folder,crop_buffer)

        break


    pass



if __name__ == "__main__":

    usage = "usage: %prog [options] polygon_shp save_dir"
    parser = OptionParser(usage=usage, version="1.0 2019-12-08")
    parser.description = 'Introduction: get time-lapse images using Google Earth Engine (GEE) '
    parser.add_option("-s", "--start_date",default='2016-01-01',
                      action="store", dest="start_date",
                      help="start date for inquiry, with format year-month-day, e.g., 2016-01-01")
    parser.add_option("-e", "--end_date",default='2019-12-31',
                      action="store", dest="end_date",
                      help="the end date for inquiry, with format year-month-day, e.g., 2019-12-31")
    parser.add_option("-c", "--cloud_cover",
                      action="store", dest="cloud_cover", type=float, default = 0.1,
                      help="the could cover threshold, only accept images with cloud cover less than the threshold")
    parser.add_option("-b", "--buffer_size",
                      action="store", dest="buffer_size", type=int, default = 500,
                      help="the buffer size to crop image in meters")
    parser.add_option("-i", "--image_type",
                      action="store", dest="image_type",default='Sentinel-2',
                      help="the image types available on GEE, e.g., COPERNICUS/S2 or COPERNICUS/S2_SR")


    (options, args) = parser.parse_args()
    if len(sys.argv) < 2 or len(args) < 1:
        parser.print_help()
        sys.exit(2)

    basic.setlogfile('get_timelapse_img_gee_%s.log' % str(datetime.date(datetime.now())))

    main(options, args)
