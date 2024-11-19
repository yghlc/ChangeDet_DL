#!/usr/bin/env python
# Filename: get_annual_poly_change.py 
"""
introduction:  calculate the annual expansion of thaw slumps in Canadian Arctic, the boundaries are saved in different the same shapefile.

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 04 November, 2024
"""

import sys,os
from optparse import OptionParser

# added path of DeeplabforRS
sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import basic_src.io_function as io_function
import basic_src.basic as basic
import basic_src.map_projection as map_projection
import parameters
from raster_statistic import zonal_stats_multiRasters

import polygons_cd
import geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import Polygon, MultiPolygon

def save_annual_polygons_to_different_files(in_shp, out_dir='./'):
    # save polygons in each year to different files
    # Read the shapefile
    gdf = gpd.read_file(in_shp)

    if os.path.isdir(out_dir) is False:
        io_function.mkdir(out_dir)

    # Ensure the 'Year' column exists
    if 'Year' not in gdf.columns:
        raise ValueError("The input shapefile must have a 'Year' column.")

    basename = io_function.get_name_no_ext(in_shp)

    # Group by year and save each group to a separate shapefile
    for year, group in gdf.groupby('Year'):
        # Define the output file path
        output_path = os.path.join(out_dir, basename + f"_{year}.shp")
        # Save the group to a shapefile
        group.to_file(output_path)


def convert_to_2d(geometry):
    # Convert Polygon Z or MultiPolygon Z to 2D
    # Convert 3D Polygons or MultiPolygons to 2D
    if geometry:
        if isinstance(geometry, Polygon):
            if geometry.has_z:
                return Polygon([(x, y) for x, y, z in geometry.exterior.coords])
        elif isinstance(geometry, MultiPolygon):
            return MultiPolygon([
                Polygon([(x, y) for x, y, z in poly.exterior.coords]) if poly.has_z else poly
                for poly in geometry.geoms
            ])
    return geometry

def track_annual_changes_of_each_thawslump(in_shp, out_dir='./'):
    # Read the shapefile
    gdf = gpd.read_file(in_shp)

    if os.path.isdir(out_dir) is False:
        io_function.mkdir(out_dir)

    # basename = io_function.get_name_no_ext(in_shp)


    # Ensure the required columns exist
    if 'Annual_ID' not in gdf.columns or 'Year' not in gdf.columns:
        raise ValueError("The input shapefile must have 'Annual_ID' and 'Year' columns.")

    # Sort by Annual_ID and Year
    gdf.sort_values(by=['Annual_ID', 'Year'], inplace=True)

    save_file_list = []

    # Group by Annual_ID
    for annual_id, group in gdf.groupby('Annual_ID'):
        # Sort each group by Year
        print(f'calculate change for rts id: {annual_id}')
        group = group.sort_values('Year')
        # print(group)
        output_path = os.path.join(out_dir, f"thawSlump_expand_Annual_ID_{annual_id}.gpkg")
        save_file_list.append(output_path)
        if os.path.isfile(output_path):
            print(f'warning, {output_path} exists, skip')
            continue

        # Initialize a list to store the annual changes
        changes = []

        # Iterate over the years and calculate changes
        previous_boundary = None
        previous_year = None
        for year, year_group in group.groupby('Year'):
            # print(year, year_group.geometry)
            # print(year, year_group)
            # in case with MultiPolygon, and convert it to 2d
            current_boundary = convert_to_2d(unary_union(year_group.geometry))
            # print(current_boundary)

            if previous_boundary is not None:
                # Calculate the difference between current and previous year's boundaries
                # only get the expanding parts, if want to get the shrinking parts, should be: previous_boundary.difference (previous_boundary)
                change = current_boundary.difference(previous_boundary)
                changes.append({'annual_id':annual_id, 'PreYear': previous_year, 'Year': year, 'Change': change,
                                'expandArea':change.area, 'Lat':year_group['Lat'].values[0], 'Long':year_group['Long'].values[0],
                                'Study_area':year_group['Study_area'].values[0]})

            previous_boundary = current_boundary
            previous_year = year

        # print(changes)
        if len(changes) < 1:
            basic.outputlogMessage(f'warning, the thaw slump: {annual_id} does have any changes, skip it')
            continue
        # Save changes to a new shapefile
        changes_gdf = gpd.GeoDataFrame(changes, crs=gdf.crs, geometry='Change')
        # output_path = f"{output_directory}/rts_changes_{annual_id}.shp"
        changes_gdf.to_file(output_path)

    return save_file_list


def add_attributes_to_slumps_expanding(in_shp, slump_expand_file_list, attribute_files, para_file):
    # add attributes from rasters to shapefiles

    # b_use_buffer_area = parameters.get_bool_parameters(para_file,'b_topo_use_buffer_area')
    # b_use_buffer_area = False
    all_touched = True

    # Read the shapefile
    gdf = gpd.read_file(in_shp)

    # Ensure the required columns exist
    if 'Annual_ID' not in gdf.columns:
        raise ValueError("The input shapefile must have 'Annual_ID' columns.")

    # Sort by Annual_ID and Year
    gdf.sort_values(by=['Annual_ID'], inplace=True)

    union_poly_path = io_function.get_name_no_ext(in_shp) + '_union.shp'
    if os.path.isfile(union_poly_path) is False:
        union_polygons = []
        # Group by Annual_ID
        for annual_id, group in gdf.groupby('Annual_ID'):
            # sort
            max_boundary = convert_to_2d(unary_union(group.geometry))
            union_polygons.append({'annual_id':annual_id,'unionPoly': max_boundary})

        # Save changes to a new shapefile
        changes_gdf = gpd.GeoDataFrame(union_polygons, crs=gdf.crs, geometry='unionPoly')

        changes_gdf.to_file(union_poly_path)
    else:
        print(f'warning, {union_poly_path} exists, skip union operation')

    # get attribute for the polygons
    stats_list = ['min', 'max', 'mean', 'median', 'std']
    process_num = 4
    tile_min_overlap = None # for each attribute, only one file
    nodata = 0
    for key in attribute_files.keys():
        if zonal_stats_multiRasters(union_poly_path,attribute_files[key],stats=stats_list,tile_min_overlap=tile_min_overlap,
                                    nodata = nodata,prefix=key,band=1,all_touched=all_touched,
                                    process_num=process_num) is False:
            return False


def get_raster_files_for_attribute(para_file):
    dem_file = parameters.get_file_path_parameters_None_if_absence(para_file,'dem_file')
    slope_file = parameters.get_file_path_parameters_None_if_absence(para_file,'slope_file')
    pisr_file = parameters.get_file_path_parameters_None_if_absence(para_file,'pisr_file')
    tpi_file = parameters.get_file_path_parameters_None_if_absence(para_file,'tpi_file')

    attributes = {'dem': dem_file,
                  'slo':slope_file,
                  'pis':pisr_file,
                  'tpi':tpi_file
                  }

    return attributes

def main(options, args):

    # the shapefile, contain annual boundaries of thaw slumps
    in_shp_path = args[0]

    assert io_function.is_file_exist(in_shp_path)
    para_file = options.para_file
    assert io_function.is_file_exist(para_file)

    # save annual polygons to individual files
    # save_annual_polygons_to_different_files(in_shp_path, out_dir='shp_each_year')

    # get the expanding of each thaw slump
    slump_expand_file_list = track_annual_changes_of_each_thawslump(in_shp_path, out_dir='thawSlump_expanding')

    raster_attribute_dict = get_raster_files_for_attribute(para_file)
    add_attributes_to_slumps_expanding(in_shp_path,slump_expand_file_list,raster_attribute_dict,para_file)

    #TODO: put the expanding and attributes together



if __name__ == "__main__":
    usage = "usage: %prog [options] shapefile "
    parser = OptionParser(usage=usage, version="1.0 2024-11-04")
    parser.description = 'Introduction: conduct change detection for polygons (annual boundary of thaw slumps) '

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

    # set parameters files
    if options.para_file is None:
        print('error, no parameters file')
        parser.print_help()
        sys.exit(2)
    else:
        parameters.set_saved_parafile_path(options.para_file)

    basic.setlogfile('polygons_changeDetection.log')

    main(options, args)


