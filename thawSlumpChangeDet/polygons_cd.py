#!/usr/bin/env python
# Filename: polygons_cd 
"""
introduction: change detection for two groups of polygons (in two shape files)

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 05 January, 2020
"""

import sys,os
from optparse import OptionParser



def main(options, args):

    pass



if __name__ == "__main__":
    usage = "usage: %prog [options] new_shape_file old_shape_file"
    parser = OptionParser(usage=usage, version="1.0 2020-01-05")
    parser.description = 'Introduction: conduct change detection for two groups of polygons '

    # parser.add_option("-p", "--para",

    #                   action="store", dest="para_file",
    #                   help="the parameters file")

    (options, args) = parser.parse_args()
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(2)

    ## set parameters files
    # if options.para_file is None:
    #     print('error, no parameters file')
    #     parser.print_help()
    #     sys.exit(2)
    # else:
    #     parameters.set_saved_parafile_path(options.para_file)

    main(options, args)



