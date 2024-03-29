#!/usr/bin/env python
# Filename: download_arcticDEM 
"""
introduction: download arcticDEM (strip or mosaic) for a specific region

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 25 December, 2020
"""

import os,sys
from optparse import OptionParser

deeplabforRS =  os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS')
sys.path.insert(0, deeplabforRS)
import vector_gpd
import basic_src.map_projection as map_projection
import basic_src.io_function as io_function
import basic_src.basic as basic

from urllib.parse import urlparse

import time

def get_total_size(url_list):
    total_size = 0
    for url in url_list:
        size = io_function.get_url_file_size(url)       # bytes
        if size is not False:
            total_size += size
    return total_size/(1024.0*1024.0*1024.0)    # GB

def main(options, args):

    extent_shp = args[0]
    dem_index_shp = args[1]
    save_folder = options.save_dir

    extent_shp_base = os.path.splitext(os.path.basename(extent_shp))[0]

    # extent polygons and projection (proj4)
    extent_shp_prj = map_projection.get_raster_or_vector_srs_info_proj4(extent_shp)
    dem_shp_prj = map_projection.get_raster_or_vector_srs_info_proj4(dem_index_shp)

    if extent_shp_prj != dem_shp_prj:
        basic.outputlogMessage('%s and %s do not have the same projection, will reproject %s'
                               %(extent_shp,dem_index_shp,os.path.basename(extent_shp)))
        epsg = map_projection.get_raster_or_vector_srs_info_epsg(dem_index_shp)
        # print(epsg)
        # extent_polys = vector_gpd.read_shape_gpd_to_NewPrj(extent_shp,dem_shp_prj.strip())
        extent_polys = vector_gpd.read_shape_gpd_to_NewPrj(extent_shp,epsg)
    else:
        extent_polys = vector_gpd.read_polygons_gpd(extent_shp)

    if len(extent_polys) < 1:
        raise ValueError('No polygons in %s'%extent_shp)
    else:
        basic.outputlogMessage('%d extent polygons in %s'%(len(extent_polys),extent_shp))

    # read dem polygons and url
    dem_polygons = vector_gpd.read_polygons_gpd(dem_index_shp)
    dem_urls = vector_gpd.read_attribute_values_list(dem_index_shp,'fileurl')

    basic.outputlogMessage('%d dem polygons in %s' % (len(dem_polygons), extent_shp))

    for idx, ext_poly in enumerate(extent_polys):
        basic.outputlogMessage('get data for the %d th extent (%d in total)' % ((idx + 1), len(extent_polys)))

        save_txt_path = os.path.join(save_folder, extent_shp_base + '_dem_urls_poly_%d.txt' % idx)
        if os.path.isfile(save_txt_path):
            urls = io_function.read_list_from_txt(save_txt_path)
            basic.outputlogMessage('read %d dem urls from %s' % (len(urls),save_txt_path))
        else:
            # get fileurl
            dem_poly_ids = vector_gpd.get_poly_index_within_extent(dem_polygons,ext_poly)
            basic.outputlogMessage('find %d DEM within %d th extent' % (len(dem_poly_ids), (idx + 1)))
            urls = [dem_urls[id] for id in dem_poly_ids]

            # save to txt
            io_function.save_list_to_txt(save_txt_path, urls)
            basic.outputlogMessage('save dem urls to %s' % save_txt_path)

        if len(urls) > 0:

            total_size_GB = get_total_size(urls)
            basic.outputlogMessage('the size of files will be downloaded is %.4lf GB for the %d th extent '%(total_size_GB,(idx+1)))
            # time.sleep(5)   # wait 5 seconds

            # download them using wget one by one
            for ii, url in enumerate(urls):
                tmp = urlparse(url)
                filename = os.path.basename(tmp.path)
                save_dem_path = os.path.join(save_folder,filename)
                if os.path.isfile(save_dem_path):
                    basic.outputlogMessage('warning, %s already exists, skip downloading'%filename)
                else:
                    # download the dem
                    basic.outputlogMessage('starting downloading %d th DEM (%d in total)'%((ii+1),len(urls)))
                    cmd_str = 'wget %s' % url
                    status, result = basic.exec_command_string(cmd_str)
                    if status != 0:
                        print(result)
                        sys.exit(status)

        else:
            basic.outputlogMessage('Warning, can not find DEMs within %d th extent'%(idx+1))



if __name__ == "__main__":

    usage = "usage: %prog [options] extent_shp dem_indexes_shp"
    parser = OptionParser(usage=usage, version="1.0 2020-12-25")
    parser.description = 'Introduction: download ArcticDEM within an extent  '
    # parser.add_option("-x", "--save_xlsx_path",
    #                   action="store", dest="save_xlsx_path",
    #                   help="save the sence lists to xlsx file")

    parser.add_option("-d", "--save_dir",
                      action="store", dest="save_dir",default='./',
                      help="the folder to save DEMs")

    (options, args) = parser.parse_args()
    if len(sys.argv) < 2 or len(args) < 1:
        parser.print_help()
        sys.exit(2)

    main(options, args)
