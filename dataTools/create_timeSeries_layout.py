#!/usr/bin/env python
# Filename: create_timeSeries_animation 
"""
introduction:

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 08 July, 2020
"""

import os, sys

sys.path.insert(0,os.path.expanduser('~/codes/PycharmProjects/DeeplabforRS'))
import basic_src.io_function as io_function
import basic_src.basic as basic

import skimage
from skimage.util import montage
import numpy as np

def main():

    # poly_%d_timeSeries
    folder_list = io_function.get_file_list_by_pattern('./','*poly_*timeSeries')

    for idx, folder in enumerate(folder_list):
        print("folder: %s"%folder)
        png_list = io_function.get_file_list_by_pattern(folder,'*.png')
        png_list.sort()

        # test
        # if '142' not in folder:
        #     continue
        count = len(png_list)
        save_path = os.path.basename(folder) + '_layout.png'
        img_array_list = []
        min_width = 100000000
        min_height = 100000000
        band = 0
        for png in png_list:
            img_array = skimage.io.imread(png)
            print(img_array.shape)
            height, width, band = img_array.shape
            if height < min_height:
                min_height = height
            if width < min_width:
                min_width = width

            img_array_list.append(img_array)

        # make sure they have the same width and height, they have similar height and width
        for idx in range(count):
            img_array_list[idx] = img_array_list[idx][0:min_height, 0:min_width, :]
        img_array_all = np.stack(img_array_list,axis=0)
        print('img_array_all shape',img_array_all.shape)

        if count <= 3:
            grid_shape = (1,count) # grid shape for the montage `(ntiles_row, ntiles_column)`
        else:
            grid_shape = None
        fill_array = [255]*band
        out_layout = montage(img_array_all,multichannel=True,grid_shape=grid_shape, fill=fill_array)

        skimage.io.imsave(save_path,out_layout)
        basic.outputlogMessage('Save to %s'%save_path)

        # test
        # break


if __name__ == "__main__":
    main()

