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

def main():

    # poly_%d_timeSeries
    folder_list = io_function.get_file_list_by_pattern('./','*poly_*timeSeries')

    for idx, folder in enumerate(folder_list):
        png_list = io_function.get_file_list_by_pattern(folder,'*.png')
        png_list.sort()

        # test
        # if '142' not in folder:
        #     continue

        save_path = os.path.basename(folder) + '.gif'

        # need to adjust dealy and loop value if necessary
        commandString = 'convert -delay 100 -loop 0 ' + ' '.join(png_list) + ' ' + save_path
        res = os.system(commandString)
        if res !=0:
            sys.exit(res)
        basic.outputlogMessage('Save to %s'%save_path)


if __name__ == "__main__":
    main()

