#!/usr/bin/env bash


## Introduction:  test and find bugs

#authors: Huang Lingcao
#email:huanglingcao@gmail.com
#add time: 01 Febuary, 2020

set -euxo pipefail


shp=~/Data/tmp_data/polygon_based_change_detection/change_blh_manu_RTS_utm_201707_36_blh_manu_RTS_utm_201807_36.shp

cal_retreat_rate.py ${shp}

# used gdb to find detailed bug information
#gdb --args python cal_retreat_rate.py ${shp}

