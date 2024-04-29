#!/usr/bin/env python3


import os
import re
# import grass.script as gscript

# import grass python libraries
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
# from grass.pygrass.modules.shortcuts import vector as v
# from grass.pygrass.modules.shortcuts import temporal as t

from osgeo import gdal

from jamr.constants import REGIONS


def parse_merit_filename(fn):
    pattern = re.compile('([ns][0-9]+)([ew][0-9]+)')
    match = pattern.search(fn)
    if match:
        lat = match.group(1)
        lon = match.group(2)
    else:
        raise ValueError(f'{fn} is not a valid MERIT DEM filename!')

    return lat, lon


def process_merit_dem(config):

    # Remove any existing mask
    try:
        r.mask(flags='r')
    except:
        pass

    # Get data directories
    scratch = config['main']['scratch']
    os.makedirs(scratch, exist_ok=True) # TEMP

    merit_data_dir = config['topography']['merit']['data_directory']

    # List MERIT DEM files
    pattern = re.compile('^[n|s][0-9]+[e|w][0-9]+_dem.tif$')
    files = os.listdir(merit_data_dir)
    merit_files = []
    for f in files:
        if pattern.match(f):
            merit_files.append(os.path.join(merit_data_dir, f))

    # Resample elevation to three coarser resolutions
    merit_rgns = ['globe_0.008333Deg', 'globe_0.004167Deg', 'globe_0.002778Deg']

    for f in merit_files:

        lat, lon = parse_merit_filename(f)

        outfiles = [os.path.join(scratch, f'merit_dem_avg_{lat}_{lon}_{rgn}.tif') for rgn in merit_rgns]

        # If the above outfiles exist then we can skip this step
        recreate = not all([os.path.exists(f) for f in outfiles])

        if not recreate:
            continue

        # Import MERIT data file
        r.in_gdal(input=f, output='merit_dem', overwrite=True, flags='a')

        for rgn in merit_rgns:
            res = REGIONS[rgn]['res']
            mapname=f'merit_dem_avg_{lat}_{lon}_{rgn}'
            g.region(raster='merit_dem', res=res)
            r.resamp_stats(input='merit_dem', output=mapname, method='average', overwrite=True)
            r.out_gdal(input=mapname, output=os.path.join(scratch, mapname + '.tif'), createopt='COMPRESS=DEFLATE', overwrite=True)

    # for rgn in merit_rgns:
    #     pattern = re.compile('.*/merit_dem_avg_([n|s][0-9]+[e|w][0-9]+)_' + rgn + '.tif')
    #     files = os.listdir(merit_data_dir)
    #     merit_files = []
    #     for f in merit_files:
    #         if pattern.match(f):
    #             merit_files.append(f)

    #     # Build VRT
    #     res = REGIONS[rgn]['res']
    #     vrt_fn = os.path.join(scratch, f'merit_dem_{rgn}.vrt')
    #     vrt_opts = gdal.BuildVRTOptions(xRes=res, yRes=res, outputBounds=(-180, -90, 180, 90))
    #     vrt = gdal.BuildVRT(vrt_fn, merit_files, options=vrt_opts)

    #     # Read data
    #     r.in_gdal(input=vrt_fn, output=f'merit_dem_{rgn}_tmp', overwrite=True, flags='a')

    #     # Fix subtle errors in bounds
    #     r.mapcalc('{r} = {a}'.format(r=f'merit_dem_{rgn}', a=f'merit_dem_{rgn}_tmp'))

    #     # Write a copy to scratch directory
    #     r.out_gdal(input=f'merit_dem_{rgn}', output=os.path.join(scratch, f'merit_dem_{rgn}.tif'), createopt='COMPRESS=DEFLATE,BIGTIFF=YES', overwrite=True)

    #     # Clean up
    #     g.remove(type='raster', name=f'merit_dem_{rgn}_tmp', flags='f')

    return 0
