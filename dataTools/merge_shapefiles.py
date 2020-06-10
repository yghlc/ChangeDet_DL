#!/usr/bin/env python
# Filename: merge_shapefiles 
"""
introduction: Merge shape files (should have the same projection)
a similar version written in bash can be found in: ~/codes/PycharmProjects/Landuse_DL/sentinelScripts/merge_shapefiles.sh

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 08 June, 2020
"""


import os, sys
sys.path.insert(0,os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))

import basic_src.io_function as io_function
import basic_src.basic as basic

from basic_src.map_projection import get_raster_or_vector_srs_info_proj4
import vector_gpd

import pandas as pd
import geopandas as gpd


def merge_shape_files(file_list, save_path):

    if len(file_list) < 1:
        raise IOError("no input shapefiles")

    ref_prj = get_raster_or_vector_srs_info_proj4(file_list[0])

    # read polygons as shapely objects
    attribute_names = None
    polygons_list = []
    polygon_attributes_list = []

    for idx, shp_path in enumerate(file_list):

        # check projection
        prj = get_raster_or_vector_srs_info_proj4(file_list[idx])
        if prj != ref_prj:
            raise ValueError('Projection inconsistent: %s is different with the first one'%shp_path)

        shapefile = gpd.read_file(shp_path)

        # go through each geometry
        for ri, row in shapefile.iterrows():
            if idx == 0 and ri==0:
                attribute_names = row.keys().to_list()
                attribute_names = attribute_names[:len(attribute_names) - 1]
                # basic.outputlogMessage("attribute names: "+ str(row.keys().to_list()))

            polygons_list.append(row['geometry'])
            polygon_attributes = row[:len(row) - 1].to_list()
            polygon_attributes_list.append(polygon_attributes)

    # save results
    save_polyons_attributes = {}
    for idx, attribute in enumerate(attribute_names):
        # print(idx, attribute)
        values = [item[idx] for item in polygon_attributes_list]
        save_polyons_attributes[attribute] = values

    save_polyons_attributes["Polygons"] = polygons_list
    polygon_df = pd.DataFrame(save_polyons_attributes)


    return vector_gpd.save_polygons_to_files(polygon_df, 'Polygons', ref_prj, save_path)


if __name__ == "__main__":
    pass