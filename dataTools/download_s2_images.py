#!/usr/bin/env python
# Filename: download_s2_images 
"""
introduction:

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 09 November, 2019
"""

import sys,os
from optparse import OptionParser
from datetime import datetime

from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
import numpy as np

# path for Landuse_DL
sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/Landuse_DL'))

#  import functions, and variable in download_planet_img (include basic, io_function in DeeplabRS)
from planetScripts.download_planet_img import *
from sentinelScripts.get_subImages import get_projection_proj4
from sentinelScripts.get_subImages import meters_to_degress_onEarth

import pandas as pd

downloaded_scenes= [] # already download images

shp_polygon_projection = None

def read_aready_download_scene(folder):
    global downloaded_scenes
    zip_list = io_function.get_file_list_by_ext('.zip', folder, bsub_folder=False)
    safe_list = io_function.get_file_list_by_ext('.SAFE', folder, bsub_folder=False)
    downloaded_scenes.extend([os.path.basename(zip).split('.')[0] for zip in zip_list] ) #zip.split('.')[0]
    downloaded_scenes.extend([os.path.basename(safe).split('.')[0] for safe in safe_list])

def add_download_scene(products):
    global downloaded_scenes
    for key, value in products.items():
        file_name = value['filename'].split('.')[0]
        downloaded_scenes.append(file_name)


def get_and_set_dhub_key(user_name=None):
    '''
    get and set the data hub account
    :return:
    '''
    keyfile = os.path.expanduser('~/.esa_d_hub_account')
    with open(keyfile) as f_obj:
        lines = f_obj.readlines()
        if user_name is None:
            tmp_str = lines[0].strip()      # # remove '\n'
            user_name, password = tmp_str.split(':')
        else:
            for line in lines:
                if user_name in line:
                    tmp_str = line.strip()
                    user_name, password = tmp_str.split(':')
                    break

        # set user name and password
        os.environ["DHUS_USER"] = user_name
        os.environ["DHUS_PASSWORD"] = password
        return True

def down_load_through_sentinel_hub():
    # it seems that through sentinel hub we can download S2 Level-2A images, but need to pay
    pass

def select_products(api, products):
    '''
    select products based on cloud and acquired time
    :param api: sentinelAPI object
    :param products: products
    :return: the selected products
    '''

    # sort product by cloud cover

    # selected by acuqired date? each year should have at least one image?
    # maybe it is not necessary, just put all the cloudless images together for the further analysis

    # GeoJSON FeatureCollection containing footprints and metadata of the scenes
    # p(api.to_geojson(products))

    # show metadata of one product
    # product_ids = [key for key, value in products.items()]
    # print(products[product_ids[0]])
    # show metadata of all product in geojson format
    # p(api.to_geojson(products))

    # print(products)       # test
    # for item in products:
    #     print(products[item])

    # Get basic information about the product: its title, file size, MD5 sum, date, footprint and
    # its download url
    # print(api.get_product_odata(product_ids[0]))
    # print(api.get_product_odata(product_ids[0],full=True))

    # # convert to Pandas DataFrame
    # products_df = api.to_dataframe(products)
    # # print(products_df)
    #
    # # sort and limit to first 5 sorted products
    # products_df_sorted = products_df.sort_values(['cloudcoverpercentage', 'beginposition'], ascending=[True, True])
    # products_df_sorted = products_df_sorted.head(5)

    selected_products = {}
    for key, value in products.items():
        # print(key, value)
        # get acquired date, could cover, file name, product id.
        scene = {}
        # get id
        scene['product_id'] = value['uuid']

        # get acquired date
        summary_str = value['summary']
        # print(summary_str)
        date_str = summary_str.split(',')[0].split(' ')[1] #.split('T')[0]      # e.g., 2015-12-19T04:32:12.03Z
        scene['acquired_date'] = date_str #  datetime.strptime(date_str, '%Y-%m-%d') # use panda for converting
        # get cloud cover
        scene['cloudcoverpercentage'] = value['cloudcoverpercentage']
        scene['filename'] = value['filename']

        selected_products[key] = scene

    # for each year, only download up to 10 images with lowest cloud cover
    date_cloud_pd = pd.DataFrame.from_dict(selected_products, orient='index') # orient='index',  columns

    # group by year, then sort by cloud cover
    date_cloud_pd['date'] = pd.to_datetime(date_cloud_pd['acquired_date'])
    date_cloud_pd = date_cloud_pd.set_index('date')
    date_cloud_pd['Year'] = date_cloud_pd.index.year

    date_cloud_pd_year_sort = date_cloud_pd.groupby(["Year"]).apply(
        lambda x: x.sort_values(["cloudcoverpercentage"], ascending=True)).reset_index(drop=True)

    selected_eachyear = date_cloud_pd_year_sort.groupby(["Year"]).head(5)   #10     # only 5

    # to list [product_id, date, cloud cover, filename, year ]
    select10_eachyear_list = selected_eachyear.values.tolist()
    # output to log file
    basic.outputlogMessage('Selected scenes:')
    for item in select10_eachyear_list:
        basic.outputlogMessage('acquired at: %s, %s, cloud per: %.3lf '%(item[1],item[3], item[2]))

    # check a scene already exist
    select10_eachyear_list_download = []
    for sel_scene in select10_eachyear_list:
        file_name_noext = sel_scene[3].split('.')[0]
        if file_name_noext not in downloaded_scenes:
            select10_eachyear_list_download.append(sel_scene)
        else:
            basic.outputlogMessage('warning, skip downloading %s because it already exists'%file_name_noext)

    download_products =  {}
    for item in select10_eachyear_list_download:
        download_products[item[0]] = products[item[0]]

    sel_products = {}
    for item in select10_eachyear_list:
        sel_products[item[0]] = products[item[0]]

    return download_products, sel_products

def crop_one_image(input_image, save_path, polygon_idx, polygon_json, buffer_size):

    from shapely.geometry import Polygon
    import rasterio
    from rasterio.mask import mask
    # json format to shapely object
    polygon_shapely = Polygon(polygon_json['coordinates'][0]).buffer(0)
    expansion_polygon = polygon_shapely.buffer(buffer_size)

    # re-projection if necessary
    img_projection = get_projection_proj4(input_image)
    if shp_polygon_projection != img_projection:
        from functools import partial
        import pyproj
        from shapely.ops import transform

        project = partial(
            pyproj.transform,
            pyproj.Proj(shp_polygon_projection),  # source coordinate system
            pyproj.Proj(img_projection))  # destination coordinate system

        expansion_polygon = transform(project, expansion_polygon)  # apply projection
        polygon_shapely = transform(project, polygon_shapely)


    # polygon_json = mapping(expansion_polygon)

    # use the rectangle
    dstnodata = 0
    # brectangle = True
    # if brectangle:
    #     # polygon_box = selected_polygon.bounds
    polygon_json = mapping(polygon_shapely.envelope)    # no buffer
    buffer_polygon_json = mapping(expansion_polygon.envelope)

    # check cloud cover, if yes, then abandon this one


    with rasterio.open(input_image) as src:

        # check image pixels, if all are dark or bright, abandon this one
        out_image_nobuffer, _ = mask(src, [polygon_json], nodata=dstnodata, all_touched=True, crop=True)
        if np.std(out_image_nobuffer) < 0.01:
            basic.outputlogMessage('Warning, Subset of Image:%s for %dth polygon is black or white,'
                                   ' skip' % (os.path.basename(input_image), polygon_idx))
            return False

        # crop image and saved to disk
        out_image, out_transform = mask(src, [buffer_polygon_json], nodata=dstnodata, all_touched=True, crop=True)

        # test: save it to disk
        out_meta = src.meta.copy()
        out_meta.update({"driver": "GTiff",
                         "height": out_image.shape[1],
                         "width": out_image.shape[2],
                         "transform": out_transform})  # note that, the saved image have a small offset compared to the original ones (~0.5 pixel)
        with rasterio.open(save_path, "w", **out_meta) as dest:
            dest.write(out_image)

    pass

def crop_produce_time_lapse_rgb_images(products, polygon_idx, polygon_json, buffer_size, download_dir, time_lapse_dir, remove_tmp=False):
    '''
    create time-lapse images for a polygon
    :param products: s2 products
    :param polygon_idx: polygon index in the shape file
    :param polygon_json: polygon in json format
    :param buffer_size: buffer size for cropping
    :param download_dir: where save the zip files
    :param time_lapse_dir: save dir
    :return:
    '''
    from zipfile import ZipFile
    import shutil

    polygon_sub_image_dir = os.path.join(time_lapse_dir,'sub_images_of_%d_polygon'%polygon_idx)
    os.system('mkdir -p ' + polygon_sub_image_dir)

    for key, value in products.items():
        file_name = value['filename']   # end with *.SAFE
        zip_name = file_name.split('.')[0]+'.zip'

        with ZipFile(os.path.join(download_dir,zip_name) , 'r') as zip_file:
            filelist = zip_file.namelist()
            # print(filelist)

            # sometime, in "filename".SAFE, the "filename" is different from zip file due to
            # retrieval from long term archive
            # get new file name of folder in the zip file
            file_name = filelist[0].split('/')[0]

            safe_folder = os.path.join(download_dir, file_name)
            # unzip if does not exist
            if os.path.isdir(safe_folder) is False:
                zip_file.extractall(download_dir)



        # find RGB images
        # jp2_list = io_function.get_file_list_by_ext('.jp2', safe_folder, bsub_folder=True)
        jp2_tci_file = io_function.get_file_list_by_pattern(safe_folder,'GRANULE/*/IMG_DATA/*_TCI.jp2')
        if len(jp2_tci_file) == 1:
            # crop to saved dir
            save_crop_name = os.path.splitext(os.path.basename(jp2_tci_file[0]))[0] + '_%d_poly.tif'%polygon_idx
            save_crop_path = os.path.join(polygon_sub_image_dir, save_crop_name)

            crop_one_image(jp2_tci_file[0], save_crop_path, polygon_idx ,polygon_json, buffer_size)

        elif len(jp2_tci_file) < 1:
            basic.outputlogMessage('warning, skip, in %s, the true color image is missing' % file_name)
        else:
            basic.outputlogMessage('warning, skip, multiple true color image in %s' % file_name)

        # remove SAFE folder to save storage
        if remove_tmp:
            shutil.rmtree(safe_folder)

        # test
        # break

    pass

def download_crop_s2_time_lapse_images(start_date,end_date, polygon_idx, polygon_json, cloud_cover_thr,
                                       buffer_size, download_dir, time_lapse_dir, remove_tmp=False):
    '''
    download all s2 images overlap with a polygon
    ref: https://sentinelsat.readthedocs.io/en/stable/api.html
    :param start_date: start date of the time lapse images
    :param end_date: end date  of the time lapse images
    :param polygon_idx: the index of polygon in the shape file
    :param polygon_json: a polygon in json format
    :param cloud_cover_thr: cloud cover for inquiring images
    :param buffer_size: buffer area for crop the image
    :param download_dir: folder to save download zip files
    :param time_lapse_dir: folder to save produce time-lapse images
    :return:
    '''

    # connect to sentienl API
    basic.outputlogMessage("connecting to sentinel API...")
    # print(os.environ["DHUS_USER"], os.environ["DHUS_PASSWORD"])
    api = SentinelAPI(os.environ["DHUS_USER"], os.environ["DHUS_PASSWORD"]) # data["login"], data["password"], 'https://scihub.copernicus.eu/dhus'

    # inquiry images
    footprint = geojson_to_wkt(polygon_json)

    products = api.query(footprint,
                         date=(start_date, end_date),  # (start, end), e.g. (“NOW-1DAY”, “NOW”)
                         platformname='Sentinel-2',
                         cloudcoverpercentage=(0, cloud_cover_thr*100)
                         )
    if len(products) < 1:
        basic.outputlogMessage('warning, no results, please increase time span or cloud cover threshold')
        return False

    download_products, selected_products = select_products(api, products)


    # download
    api.download_all(download_products, download_dir)

    # add the downloaded file name to "downloaded_scenes"
    add_download_scene(download_products)

    # crop and produce time-lapse images
    crop_produce_time_lapse_rgb_images(selected_products, polygon_idx, polygon_json, buffer_size, download_dir, time_lapse_dir, remove_tmp=remove_tmp)

    test = 1
    pass

def download_s2_by_tile():
    # test download

    # For orthorectified products (Level-1C and Level-2A):
    # The granules (also called tiles) consist of 100 km by 100 km squared ortho-images in
    # UTM/WGS84 projection. There is one tile per spectral band.
    # For Level-1B, a granule covers approximately 25 km AC and 23 km AL
    # Tiles are approximately 500 MB in size.
    # Tiles can be fully or partially covered by image data. Partially covered tiles
    # correspond to those at the edge of the swath.

    # All data acquired by the MSI instrument are systematically processed up to Level-1C by the ground segment,
    # specifically the Payload Data Ground Segment (PDGS). Level-2A products are
    # generated on user side through the Sentinel-2 Toolbox.

    #Level-2A products are not systematically generated at the ground segment.
    # Level-2A generation can be performed by the user through the Sentinel-2 Toolbox using
    # as input the associated Level-1C product.

    #Level-0 and Level-1A products are PDGS internal products not made available to users.

    # example from https://sentinelsat.readthedocs.io/en/stable/api.html

    from collections import OrderedDict

    api = SentinelAPI(os.environ["DHUS_USER"], os.environ["DHUS_PASSWORD"])

    tiles = ['33VUC', '33UUB']

    query_kwargs = {
        'platformname': 'Sentinel-2',
        'producttype': 'S2MSI1C',
        'date': ('NOW-14DAYS', 'NOW')}

    products = OrderedDict()
    for tile in tiles:
        kw = query_kwargs.copy()
        kw['tileid'] = tile  # products after 2017-03-31
        pp = api.query(**kw)
        products.update(pp)

    api.download_all(products)

def main(options, args):

    polygons_shp = args[0]
    save_folder = args[1]  # folder for saving downloaded images

    # check training polygons
    assert io_function.is_file_exist(polygons_shp)
    os.system('mkdir -p ' + save_folder)

    download_save_dir = os.path.join(save_folder, 's2_download')
    time_lapse_dir = os.path.join(save_folder, 's2_time_lapse_images')
    os.system('mkdir -p ' + download_save_dir)
    os.system('mkdir -p ' + time_lapse_dir)

    # item_types = options.item_types.split(',') # ["PSScene4Band"]  # , # PSScene4Band , PSOrthoTile

    start_date = datetime.strptime(options.start_date, '%Y-%m-%d') #datetime(year=2018, month=5, day=20)
    end_date = datetime.strptime(options.end_date, '%Y-%m-%d')  #end_date
    cloud_cover_thr = options.cloud_cover           # 0.3
    rm_temp = options.remove_tmp

    # check these are EPSG:4326 projection
    global shp_polygon_projection
    shp_polygon_projection = get_projection_proj4(polygons_shp)
    if shp_polygon_projection == '+proj=longlat +datum=WGS84 +no_defs':
        crop_buffer = meters_to_degress_onEarth(options.buffer_size)
    else:
        crop_buffer = options.buffer_size

    # set account
    if get_and_set_dhub_key() is not True:
        return False

    # read polygons
    polygons_json = read_polygons_json(polygons_shp)

    #
    read_aready_download_scene(download_save_dir)

    # test
    # download_s2_by_tile()

    for idx, geom in enumerate(polygons_json):
        basic.outputlogMessage('downloading and cropping images for %dth polygon, total: %d polygons'%
                               (idx+1, len(polygons_json)))
        download_crop_s2_time_lapse_images(start_date, end_date, idx, geom, cloud_cover_thr,
                                           crop_buffer, download_save_dir,time_lapse_dir,remove_tmp=rm_temp)

        break

    pass



if __name__ == "__main__":

    usage = "usage: %prog [options] polygon_shp save_dir"
    parser = OptionParser(usage=usage, version="1.0 2019-11-09")
    parser.description = 'Introduction: search and download Sentinel-2 images and crop to polyon extents '
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

    parser.add_option("-r", "--remove_tmp",
                      action="store_true", dest="remove_tmp", default=False,
                      help="set this flag to remove temporary files or folders")

    # parser.add_option("-i", "--item_types",
    #                   action="store", dest="item_types",default='PSScene4Band',
    #                   help="the item types, e.g., PSScene4Band,PSOrthoTile")


    (options, args) = parser.parse_args()
    if len(sys.argv) < 2 or len(args) < 1:
        parser.print_help()
        sys.exit(2)

    basic.setlogfile('download_s2_images_%s.log' % str(datetime.date(datetime.now())))

    main(options, args)
