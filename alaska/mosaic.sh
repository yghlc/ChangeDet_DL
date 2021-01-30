#!/bin/bash

#~/codes/PycharmProjects/ChangeDet_DL/QZroad_2019_inventory/create_mosaic.sh

out_res=3
#out_res=30

sr_max=2000
sr_min=0

cloud_cover=0.3
# due to memory issues, we should not set this too high
process_num=4

dir=~/Data/Arctic/alaska/rs_images/planet_sr_images/2020_Jul_Aug
#grid_shp=~/Data/Arctic/alaska/northern_alaska_extent/NoAK_LandscapePermafrost_11242014_edit_buff100_small.shp
grid_shp=~/Data/Arctic/alaska/northern_alaska_extent/NoAK_LandscapePermafrost_11242014_edit_buff100_small_edit.shp

# --to_rgb
# --group_date
~/codes/PycharmProjects/ChangeDet_DL/dataTools/mosaic_images_crop_grid.py ${dir} ${grid_shp} -r ${out_res} -u ${sr_max} -l ${sr_min} -c ${cloud_cover} -p ${process_num} --group_date


# remove tmp folders
rm -r RGB_images_*
rm -r planet_images_reproj_*

