#!/usr/bin/env python
# Filename: plot_planetImg_histogram 
"""
introduction: plot histogram of all the Planet images

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 07 January, 2021
"""

import os, sys
from optparse import OptionParser

HOME = os.path.expanduser('~')
# path of DeeplabforRS
codes_dir2 =  HOME +'/codes/PycharmProjects/DeeplabforRS'
sys.path.insert(0, codes_dir2)

import basic_src.io_function as io_function
import basic_src.basic as basic
import raster_io

import numpy as np
import matplotlib.pyplot as plt

def np_histogram_one_image(tif_path, axis_range, bin_count):

    # read tif
    img_data_allBands, nodata = raster_io.read_raster_all_bands_np(tif_path)  # (bandcount, height, width)
    nband, width, height = img_data_allBands.shape
    print('nband, width, height', nband, width, height)
    data = img_data_allBands.reshape(nband,-1)
    print('data.shape', data.shape)


    hist_list = []
    bin_edges = None
    for index in range(nband):
        one_band_data = data[index,:]
        if nodata is not None:
            one_band_data = one_band_data[ one_band_data!= nodata]  # remove nodata values
        hist, bin_edges = np.histogram(one_band_data,bins=bin_count,density=False,range=axis_range)
        hist_list.append(hist)
        # print(bin_edges)

    return hist_list, bin_edges


def main(options, args):

    img_dir = args[0]
    tif_list = io_function.get_file_list_by_ext('.tif',img_dir,bsub_folder=True)
    if len(tif_list) < 1:
        raise ValueError('no tif in %s'%img_dir)

    range = (1, 6000)
    bin_count = 500

    # plot histograms for each band
    hist_allImg_list = []
    bin_edges = None
    for idx, tif in enumerate(tif_list):
        print(idx,len(tif_list), tif)
        hist_list, bin_edges = np_histogram_one_image(tif, range, bin_count)

        bin_edges = bin_edges # we have the fix range, so the bin_edges should be fix
        if len(hist_allImg_list) < 1:
            hist_allImg_list = hist_list
            # print(hist_allImg_list)
        else:
            # accumulate the hist
            if len(hist_allImg_list) != len(hist_list):
                raise ValueError('image band count of %s is different from the previous ones'%tif)
            for hist_all, hist in zip(hist_allImg_list,hist_list):
                hist_all += hist
                # print(hist_all)

        # # test
        # if idx > 200:
        #     break


    fig = plt.figure(figsize=(6,4)) #
    ax1 = fig.add_subplot(111)
    # ax2 = ax1.twiny()    #have another x-axis

    # ax1.yaxis.tick_right()

    # line_list = []
    line_style = ['b-','g-','r-','r-.']
    values_x = bin_edges[:-1]  # ignore the last one
    for idx, hist in enumerate(hist_allImg_list):
    # plot histogram
        values_per = 100.0 * hist / np.sum(hist) # draw the percentage
        line, = ax1.plot(values_x, values_per,line_style[idx], label="Band %d"%(idx+1), linewidth=0.8)

    # ax2.set_xlabel("Elevation (m)",color="red",fontsize=15)
    # ax2.spines['bottom'].set_color('blue')
    # ax1.spines['top'].set_color('red')
    # ax2.xaxis.label.set_color('blue')
    ax1.tick_params(axis='x')

    # ## marked the values
    # threshold = [9500]
    # for dem in threshold:
    #     ax1.axvline(x=dem, color='r', linewidth=0.8, linestyle='--')
    #     ax1.text(dem + 100, 0.5, str(dem), rotation=90, fontsize=10, color='r')


    # plt.gcf().subplots_adjust(bottom=0.15)  #add space for the buttom
    # plt.gcf().subplots_adjust(top=0.8)  # the value range from [0,1], 1 is toppest, 0 is bottom
    # plt.gcf().subplots_adjust(left=0.15)
    # plt.gcf().subplots_adjust(right=0.15)

    ax1.legend(fontsize=10, loc="best")  # loc="upper left"
    ax1.set_xlabel('grey values')
    ax1.set_ylabel('%')

    # fig.legend((line_slope,line_dem),('Slope Histogram', 'DEM Histogram'))
    # ax1.legend(line_dem, ('Gray value'), fontsize=16,loc='upper center')

    save_path = os.path.basename(img_dir) +'_bin%d'%bin_count + '_range_%d_%d'%(range[0],range[1]) + '.jpg'
    plt.savefig(save_path, dpi=200)  # 300

    pass

if __name__ == '__main__':
    usage = "usage: %prog [options] image_folder "
    parser = OptionParser(usage=usage, version="1.0 2021-01-07")
    parser.description = 'Introduction: plot histogram of images '

    # parser.add_option("-x", "--save_xlsx_path",
    #                   action="store", dest="save_xlsx_path",
    #                   help="save the sence lists to xlsx file")

    (options, args) = parser.parse_args()
    # print(options.create_mosaic)

    if len(sys.argv) < 2 or len(args) < 1:
        parser.print_help()
        sys.exit(2)

    main(options, args)

