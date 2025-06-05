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
import re

# added path of DeeplabforRS
sys.path.insert(0, os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import basic_src.io_function as io_function
import basic_src.basic as basic
import basic_src.map_projection as map_projection
import vector_gpd
import parameters
from raster_statistic import zonal_stats_multiRasters

import polygons_cd
import pandas as pd
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
        if os.path.isfile(output_path):
            print(f'warning, {output_path} exists, skip')
            save_file_list.append(output_path)
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
            basic.outputlogMessage(f'warning, the thaw slump: {annual_id} does not have any changes, skip it')
            continue
        # Save changes to a new shapefile
        changes_gdf = gpd.GeoDataFrame(changes, crs=gdf.crs, geometry='Change')
        # output_path = f"{output_directory}/rts_changes_{annual_id}.shp"
        changes_gdf.to_file(output_path)
        save_file_list.append(output_path)

    return save_file_list


def test_calculate_retreat_distance_medial_axis():
    data_dir = os.path.expanduser('~/Data/Arctic/canada_arctic/shp_slumps_growth/polygon_changeDet')
    # test_file = os.path.join(data_dir,'thawSlump_expanding','thawSlump_expand_Annual_ID_312.gpkg')
    # test_file = os.path.join(data_dir,'thawSlump_expanding','thawSlump_expand_Annual_ID_218.gpkg')
    # test_file = os.path.join(data_dir,'thawSlump_expanding','thawSlump_expand_Annual_ID_115.gpkg')
    # calculate_retreat_distance_medial_axis([test_file])


    expand_shp_files = io_function.get_file_list_by_pattern(data_dir,'thawSlump_expanding/*.gpkg')
    calculate_retreat_distance_medial_axis(expand_shp_files)


def calculate_retreat_distance_medial_axis(input_files):
    # calculate the retreat distance of expanding areas by using medial axis
    # input_files: files contain annual expand areas of each RTS

    from polygons_cd import  Multipolygon_to_Polygons
    from cal_retreat_rate import cal_expand_area_distance

    for idx, in_file in enumerate(input_files):
        print(f'({idx+1}/{len(input_files)}) calculating retreat distance for {os.path.basename(in_file)}')
        save_medial_axis = io_function.get_name_by_adding_tail(in_file,'medial_axis')
        all_change_polygons = os.path.join(os.path.dirname(in_file),io_function.get_name_no_ext(in_file)  + '_all_changes.shp')

        Multipolygon_to_Polygons(in_file,all_change_polygons)
        vector_gpd.check_remove_None_geometries_file(all_change_polygons,all_change_polygons)
        cal_expand_area_distance(all_change_polygons,proc_num=None, save_medial_axis=save_medial_axis)







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

    return union_poly_path

def get_raster_files_for_attribute(para_file):
    dem_file = parameters.get_file_path_parameters_None_if_absence(para_file,'dem_file')
    slope_file = parameters.get_file_path_parameters_None_if_absence(para_file,'slope_file')
    pisr_file = parameters.get_file_path_parameters_None_if_absence(para_file,'pisr_file')
    tpi_file = parameters.get_file_path_parameters_None_if_absence(para_file,'tpi_file')
    geosurface_file = parameters.get_file_path_parameters_None_if_absence(para_file,'geosurface_file')

    attributes = {'dem': dem_file,
                  'slo':slope_file,
                  'pis':pisr_file,
                  'tpi':tpi_file,
                  'sur':geosurface_file
                  }

    return attributes

def read_annual_expand_a_slump(slump_expand_shp, start_year, end_year):
    # read annual expand area in a shapefile into dict

    attribute_2d = vector_gpd.read_attribute_values_list_2d(slump_expand_shp,
            ['annual_id','PreYear','Year','expandArea','Lat','Long', 'Study_area'])

    # print(slump_expand_shp)
    # print(attribute_2d)
    expand_dict = {'annual_id': attribute_2d[0][0],
                   'Lat':attribute_2d[4][0],
                   'Long':attribute_2d[5][0],
                   'Study_area':attribute_2d[6][0]
                   }
    for year in range(start_year,end_year+1):
        # print(year)
        expand_dict[str(year)+'eArea'] = -1

    # add the expanding areas (this year - last year)
    for year, expandArea in zip(attribute_2d[2],attribute_2d[3]):
        expand_dict[str(year)+'eArea'] = expandArea

    # print(expand_dict)
    return expand_dict

def assemble_expansion_and_attributes(org_shp, slump_expand_file_list, attribute_shp, save_path=None):
    # combine the annual expansion of each slump and attributes into one file
    year_list = vector_gpd.read_attribute_values_list(org_shp,'Year')
    start_year = min(year_list)
    end_year = max(year_list)

    # read expanding information for each thaw slump
    expand_info_list = []
    for idx, expand_shp in enumerate(slump_expand_file_list):
        # print(idx)
        expand_info = read_annual_expand_a_slump(expand_shp, start_year, end_year)
        expand_info_list.append(expand_info)

    # Convert the list of dictionaries to a DataFrame
    expand_info_df = pd.DataFrame(expand_info_list)

    ## merge the information into the attribute_shp
    attr_gdf = gpd.read_file(attribute_shp)

    # Merge the new information into the GeoDataFrame
    # The merge is performed on the 'annual_id' field
    gdf = attr_gdf.merge(expand_info_df, on="annual_id", how="left")

    if save_path is None:
        save_path = io_function.get_name_by_adding_tail(attribute_shp,'expandArea')
    gdf.to_file(save_path)
    basic.outputlogMessage(f'save to {save_path}')

    return save_path


def read_climate_data_list(data_dir):
    csv_list = io_function.get_file_list_by_pattern(data_dir,'*.csv')
    climate_files_dict = {}
    for csv in csv_list:
        match = re.search(r'\d+', os.path.basename(csv))
        if match:
            id_digits = match.group()  # Extract the matched digits as a string
            # print(digits)  # Output: 83
        else:
            raise ValueError(f'there is id in the file name: {os.path.basename(csv)}')
        climate_files_dict[int(id_digits)]  = csv

    return climate_files_dict

def add_meteorological_variables(slump_expand_shp, climate_dir, save_dir=None):
    # read and add _meteorological data from csv files to shapefile
    # do not save to shape file, but save to an excel file

    slump_ids = vector_gpd.read_attribute_values_list(slump_expand_shp,'annual_id')
    slump_areas = vector_gpd.read_attribute_values_list(slump_expand_shp,'Study_area')
    climate_files_dict = read_climate_data_list(climate_dir)

    # variables to read (ClimateNA -> name) # more on: https://climatena.ca/Help2
    # qustions:
    # Max Summer Precip (MSP??, then calculate the max?), which one should be used?
    # how about Thawing Degree Days (DD5?), Freezing Degree Days (DD_0?)?
    variable_names = {'MAT': 'Mean Annual Temp ',
                      'Tave_sm': 'Mean Summer temp ',
                      'PPT_sm': 'summer precipitation', #  Total Summer Precip ?
                      'PPT_wt': 'winter precipitation', # Total Winter Precip ?
                      'Tmax_sm': 'summer mean maximum temperature', # Max Summer Temp
                      'DD5': 'degree-days above 5',
                      'DD_0': 'degree-days below 0'
                      }

    if save_dir is None:
        save_dir = 'climate_data'
    if os.path.isdir(save_dir) is False:
        io_function.mkdir(save_dir)

    #TODO: get these valuables for each slump
    start_year = 2000
    end_year = 2024
    for key in variable_names.keys():

        save_path = os.path.join(save_dir, key + '.xlsx')
        if os.path.isfile(save_path):
            basic.outputlogMessage(f'{save_path} exists, would replace it')
            # continue

        # create a dict for tables
        var_table = {'Annual_ID': [],
                     'Lat': [],
                     'Long': [],
                     'elev':[]}
        for year in range(start_year, end_year):  # 2000 to 2023
            var_table[f'Year_{year}.ann'] = []

        for s_id, stu_area in zip(slump_ids, slump_areas):
            csv_df = pd.read_csv(climate_files_dict[s_id])
            csv_df.columns = csv_df.columns.str.replace(" ", "", regex=False)   # remove space in column names
            # print(csv_df.keys())
            # break
            # print(csv_df)
            period = csv_df['period']
            key_values = csv_df[key]
            lat_var = csv_df['Lat']
            long_var = csv_df['long']
            elev_var = csv_df['elev']

            var_table['Annual_ID'].append(s_id)
            var_table['Lat'].append(float(lat_var.iloc[0]))
            var_table['Long'].append(float(long_var.iloc[0]))
            var_table['elev'].append(float(elev_var.iloc[0]))

            # Create a dictionary for current year's key-value pairs
            # duplicate keys in the period column will result in only the last value being retained in the dictionary.
            year_value_map = dict(zip(period, key_values))
            # print(year_value_map)

            # Append values for each year, filling missing years with None
            for year in range(start_year, end_year):
                year_key = f'Year_{year}.ann'
                if year_key in year_value_map:
                    var_table[year_key].append(year_value_map[year_key])
                else:
                    var_table[year_key].append(None)  # Fill with None for missing years

            # for year_str, key_var in zip(period,key_values):
            #     # print(year_str, key_var)
            #     var_table[year_str].append(key_var)
            #     # break

            # print(var_table)
            # break

        # Convert the dictionary to a pandas DataFrame
        save_df = pd.DataFrame(var_table)

        # Save the DataFrame to an Excel file
        save_df.to_excel(save_path, index=False)  # Set `index=False` to exclude the index column
        basic.outputlogMessage(f'save to {save_path}')



def add_meteorological_variables_from_a_csv_file(slump_expand_shp, climate_csv_file, save_dir=None):
    # add meteorological variables from a single csv file
    # this csv file is exported from the window version of ClimateNA

    slump_ids = vector_gpd.read_attribute_values_list(slump_expand_shp, 'annual_id')
    slump_areas = vector_gpd.read_attribute_values_list(slump_expand_shp, 'Study_area')

    # variables to read (ClimateNA -> name) # more on: https://climatena.ca/Help2
    # qustions:
    # Max Summer Precip (MSP??, then calculate the max?), which one should be used?
    # how about Thawing Degree Days (DD5?), Freezing Degree Days (DD_0?)?
    variable_names = {'MAT': 'Mean Annual Temp ',
                      'Tave_sm': 'Mean Summer temp ',
                      'PPT_sm': 'summer precipitation',  # Total Summer Precip ?
                      'PPT_wt': 'winter precipitation',  # Total Winter Precip ?
                      'Tmax_sm': 'summer mean maximum temperature',  # Max Summer Temp
                      'DD5': 'degree-days above 5',
                      'DD_0': 'degree-days below 0'
                      }

    if save_dir is None:
        save_dir = 'climate_data'
    if os.path.isdir(save_dir) is False:
        io_function.mkdir(save_dir)

    csv_df = pd.read_csv(climate_csv_file)

    # get these valuables for each slump
    start_year = 2000
    end_year = 2024
    for key in variable_names.keys():

        save_path = os.path.join(save_dir, key + '.xlsx')
        if os.path.isfile(save_path):
            basic.outputlogMessage(f'{save_path} exists, would replace it')
            # continue

        # create a dict for tables
        var_table = {'Annual_ID': [],
                     'Latitude': [],
                     'Longitude': [],
                     'Elevation': [],
                     'studyArea':[]
                     }
        for year in range(start_year, end_year):  # 2000 to 2023
            var_table[year] = []

        for s_id, stu_area in zip(slump_ids, slump_areas):

            filtered_df = csv_df[csv_df['id1'] == s_id]
            sel_df = filtered_df[[key,'Year','Latitude', 'Longitude','Elevation']]

            # Year = csv_df['period']
            # key_values = csv_df[key]
            # lat_var = csv_df['Lat']
            # long_var = csv_df['long']
            # elev_var = csv_df['elev']

            var_table['Annual_ID'].append(s_id)
            var_table['Latitude'].append(float(sel_df['Latitude'].iloc[0]))
            var_table['Longitude'].append(float(sel_df['Longitude'].iloc[0]))
            var_table['Elevation'].append(float(sel_df['Elevation'].iloc[0]))
            var_table['studyArea'].append(stu_area)

            # Create a dictionary for current year's key-value pairs
            # duplicate keys in the period column will result in only the last value being retained in the dictionary.
            year_value_map = dict(zip(sel_df['Year'], sel_df[key]))
            # print(year_value_map)

            # Append values for each year, filling missing years with None
            for year in range(start_year, end_year):
                if year in year_value_map:
                    var_table[year].append(year_value_map[year])
                else:
                    var_table[year].append(None)  # Fill with None for missing years


        # Convert the dictionary to a pandas DataFrame
        save_df = pd.DataFrame(var_table)

        # Save the DataFrame to an Excel file
        save_df.to_excel(save_path, index=False)  # Set `index=False` to exclude the index column
        basic.outputlogMessage(f'save to {save_path}')


def test_assemble_expansion_and_attributes():
    data_dir = os.path.expanduser('~/Data/Arctic/canada_arctic/shp_slumps_growth')
    org_shp = os.path.join(data_dir,'Planet_ThawSlumps_Sept26_24_with_Prj.shp')
    slump_expand_file_list = io_function.get_file_list_by_pattern(data_dir,'polygon_changeDet/thawSlump_expanding/*.gpkg')
    attribute_shp = os.path.join(data_dir,'polygon_changeDet','Planet_ThawSlumps_Sept26_24_with_Prj_union.shp')

    assemble_expansion_and_attributes(org_shp, slump_expand_file_list, attribute_shp)


def test_add_meteorological_variables():
    data_dir = os.path.expanduser('~/Data/Arctic/canada_arctic/shp_slumps_growth')
    slump_expand_shp = os.path.join(data_dir,'polygon_changeDet',
                                    'Planet_ThawSlumps_Sept26_24_with_Prj_union_expandArea.shp')
    climate_dir = 'climate_data'
    add_meteorological_variables(slump_expand_shp, climate_dir)

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
    slump_exp_attr_shp = add_attributes_to_slumps_expanding(in_shp_path,slump_expand_file_list,raster_attribute_dict,para_file)
    if slump_exp_attr_shp is False:
        return

    #put the expanding and attributes together
    slump_expArea_attr_shp = assemble_expansion_and_attributes(in_shp_path, slump_expand_file_list,slump_exp_attr_shp)

    # add meteorological variables
    climate_dir = 'climate_data'
    # add_meteorological_variables(slump_expArea_attr_shp, climate_dir)
    climate_csv_file = os.path.join('climate_data','site_locations_2000-2023MSY.csv')
    add_meteorological_variables_from_a_csv_file(slump_expArea_attr_shp,climate_csv_file)


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

    # test_assemble_expansion_and_attributes()
    # test_add_meteorological_variables()
    test_calculate_retreat_distance_medial_axis()
    sys.exit(0)

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


