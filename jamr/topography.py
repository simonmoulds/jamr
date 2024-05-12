#!/usr/bin/env python3

import os
import re
import glob
import time
# import grass.script as gscript

import grass.exceptions 

# import grass python libraries
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r

from osgeo import gdal

from jamr.constants import REGIONS


def process_topographic_index(config, overwrite = False):
    
    g.region(region='globe_0.004167Deg')
    marthews_data_dir = config['topography']['marthews']['data_directory']
    r.in_gdal(input=os.path.join(marthews_data_dir, 'data-raw', 'ga2.tif'), output='marthews_topidx', flags='a', overwrite=overwrite)
    r.mapcalc('marthews_topidx_globe_0.004167Deg = marthews_topidx', overwrite=overwrite)
    # TODO compare Marthews dataset with r.topidx values? 

    # # Hydrography90m data - compare against Marthews dataset 
    # hydrography_data_dir = config['topography']['hydrography90m']['data_directory']
    # pattern = re.compile('^cti_h[0-9]+v[0-9]+.tif$')
    # files = os.listdir(hydrography_data_dir)
    # cti_files = []
    # for f in files:
    #     if pattern.match(f):
    #         cti_files.append(os.path.join(hydrography_data_dir, f))
    # # Build VRT
    # res = 1 / 1200.
    # vrt_fn = os.path.join(scratch, f'cti_{rgn}.vrt')
    # vrt_opts = gdal.BuildVRTOptions(xRes=res, yRes=res, outputBounds=(-180, -90, 180, 90))
    # my_vrt = gdal.BuildVRT(vrt_fn, cti_files, options=vrt_opts)
    # my_vrt = None 
    # TODO fill holes in Hydrography90m dataset? 

    return 0