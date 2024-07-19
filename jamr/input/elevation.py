#!/usr/bin/env python3

import os
import re
import glob

from abc import ABC, abstractmethod

import grass.script as gscript
import grass.exceptions 

# import grass python libraries
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r

from osgeo import gdal

from jamr.utils.utils import grass_maplist
from jamr.utils.constants import REGIONS
from jamr.input.dataset import DS


def parse_merit_filename(fn):
    pattern = re.compile('([ns][0-9]+)([ew][0-9]+)')
    match = pattern.search(fn)
    if match:
        lat = match.group(1)
        lon = match.group(2)
    else:
        raise ValueError(f'{fn} is not a valid MERIT DEM filename!')

    return lat, lon


class MERITDEM(DS):
    def __init__(self, config, overwrite):
        self.merit_regions = ['globe_0.008333Deg', 'globe_0.004167Deg', 'globe_0.002778Deg']
        super().__init__(config, overwrite)

    def initial(self):
        self.preprocess()
        self.read()

    def get_input_filenames(self):
        data_directory = self.config['topography']['merit']['data_directory']
        filenames = []
        pattern = re.compile('^[n|s][0-9]+[e|w][0-9]+_dem.tif$')
        files = glob.glob(data_directory + '/**/*.tif', recursive=True)
        for f in files:
            fpath, fname = os.path.split(f)
            if pattern.match(fname):
                filenames.append(os.path.join(fpath, fname))
        self.filenames = filenames 

    def set_mapnames(self):
        mapnames = {} 
        for rgn in self.merit_regions:
            mapnames[rgn] = f'merit_dem_{rgn}'
        self.mapnames = mapnames

    def preprocess(self):
        scratch = self.config['main']['scratch_directory']
        os.makedirs(scratch, exist_ok=True) # Just in case it's not been created yet
        preprocessed_filenames = {}
        for rgn in self.merit_regions:

            resolution = REGIONS[rgn]['res']
            rgn_filenames = []
            for f in self.filenames:
                lat, lon = parse_merit_filename(f)
                mapname=f'merit_dem_avg_{lat}_{lon}_{rgn}'
                outfile = os.path.join(scratch, f'merit_dem_avg_{lat}_{lon}_{rgn}.tif')
                rgn_filenames.append(outfile)
                if os.path.exists(outfile) and not self.overwrite:
                    continue 
                
                # Import MERIT data file [note overwrite=True]
                r.in_gdal(input=f, output=f'merit_dem', flags='a', overwrite=True)

                # for rgn in merit_regions:
                g.region(raster='merit_dem', res=resolution)
                try:
                    r.resamp_stats(input='merit_dem', output=mapname, method='average', overwrite=True)
                except grass.exceptions.CalledModuleError:
                    pass
                r.out_gdal(input=mapname, output=outfile, createopt='COMPRESS=DEFLATE', overwrite=True)

            # Build VRT
            vrt_fn = os.path.join(scratch, f'merit_dem_{rgn}.vrt')
            preprocessed_filenames[rgn] = vrt_fn
            if os.path.exists(vrt_fn) and not self.overwrite:
                continue

            # If overwrite or the file doesn't exist then we build the VRT file
            vrt_opts = gdal.BuildVRTOptions(xRes=resolution, yRes=resolution, outputBounds=(-180, -90, 180, 90))
            my_vrt = gdal.BuildVRT(vrt_fn, rgn_filenames, options=vrt_opts)
            my_vrt = None # This is necessary to write the file
        
        self.preprocessed_filenames = preprocessed_filenames

    def read(self):
        for rgn in self.merit_regions: 
            input_filename = self.preprocessed_filenames[rgn]
            mapname = self.mapnames[rgn]

            maplist = grass_maplist(pattern=mapname)
            if (len(maplist) == 1) and not self.overwrite:
                continue

            try:
                r.in_gdal(input=input_filename, output=mapname + '_tmp', flags='a', overwrite=True)
            except grass.exceptions.CalledModuleError:
                pass 

            # This is needed to fix subtle errors in bounds
            # FIXME - see whether this is still needed even with the 'a' flag to r.in.gdal
            try:
                r.mapcalc(f'{mapname} = {mapname}_tmp', overwrite=True)
            except grass.exceptions.CalledModuleError:
                pass 

            # # Write a copy to scratch directory
            # r.out_gdal(input=f'merit_dem_{rgn}', output=os.path.join(scratch, f'merit_dem_{rgn}.tif'), createopt='COMPRESS=DEFLATE,BIGTIFF=YES', overwrite=True)

            # Clean up
            g.remove(type='raster', name=f'{mapname}_tmp', flags='f')

            # TODO this should be separate from the input dataset 
            # # Create slope map [needed for PDM] 
            # try:
            #     r.slope_aspect(elevation='merit_dem_globe_0.004167Deg', slope='merit_dem_slope_globe_0.004167Deg', format='degrees', overwrite=overwrite)
            # except grass.exceptions.CalledModuleError:
            #     pass 


# def process_merit_dem(config, overwrite=False):

#     # Remove any existing mask
#     try:
#         r.mask(flags='r')
#     except grass.exceptions.CalledModuleError:
#         pass

#     # Get data directories
#     scratch = config['main']['scratch_directory']
#     os.makedirs(scratch, exist_ok=True) # TEMP

#     merit_data_dir = config['topography']['merit']['data_directory']

#     # List MERIT DEM files
#     pattern = re.compile('^[n|s][0-9]+[e|w][0-9]+_dem.tif$')
#     files = glob.glob(merit_data_dir + '/**/*.tif', recursive=True)
#     merit_files = []
#     for f in files:
#         fpath, fname = os.path.split(f)
#         if pattern.match(fname):
#             merit_files.append(os.path.join(fpath, fname))

#     # Resample elevation to three coarser resolutions
#     merit_rgns = ['globe_0.008333Deg', 'globe_0.004167Deg', 'globe_0.002778Deg']

#     for f in merit_files:
#         lat, lon = parse_merit_filename(f)
#         outfiles = [os.path.join(scratch, f'merit_dem_avg_{lat}_{lon}_{rgn}.tif') for rgn in merit_rgns]

#         # If the above outfiles exist then we can skip this step
#         recreate = not all([os.path.exists(f) for f in outfiles])
#         if not recreate or overwrite:
#             continue

#         # Import MERIT data file
#         r.in_gdal(input=f, output=f'merit_dem', overwrite=True, flags='a')

#         for rgn in merit_rgns:
#             res = REGIONS[rgn]['res']
#             mapname=f'merit_dem_avg_{lat}_{lon}_{rgn}'
#             g.region(raster='merit_dem', res=res)
#             r.resamp_stats(input='merit_dem', output=mapname, method='average', overwrite=True)
#             r.out_gdal(input=mapname, output=os.path.join(scratch, mapname + '.tif'), createopt='COMPRESS=DEFLATE', overwrite=True)

#     for rgn in merit_rgns:

#         # # Dump list of file names to file
#         # g.list(type='raster', pattern=f'merit_dem_avg_*_{rgn}', output='/tmp/tilelist.csv', overwrite=True)

#         pattern = re.compile('^merit_dem_avg_[n|s][0-9]+_[e|w][0-9]+_' + rgn + '.tif$')
#         files = os.listdir(scratch)
#         merit_files = []
#         for f in files:
#             if pattern.match(f):
#                 merit_files.append(os.path.join(scratch, f))

#         # Build VRT
#         res = REGIONS[rgn]['res']
#         vrt_fn = os.path.join(scratch, f'merit_dem_{rgn}.vrt')
#         vrt_opts = gdal.BuildVRTOptions(xRes=res, yRes=res, outputBounds=(-180, -90, 180, 90))
#         my_vrt = gdal.BuildVRT(vrt_fn, merit_files, options=vrt_opts)
#         my_vrt = None 

#         # Read data
#         r.in_gdal(input=vrt_fn, output=f'merit_dem_{rgn}_tmp', overwrite=True, flags='a')

#         # Fix subtle errors in bounds
#         r.mapcalc('{r} = {a}'.format(r=f'merit_dem_{rgn}', a=f'merit_dem_{rgn}_tmp'), overwrite=True)

#         # # Write a copy to scratch directory
#         # r.out_gdal(input=f'merit_dem_{rgn}', output=os.path.join(scratch, f'merit_dem_{rgn}.tif'), createopt='COMPRESS=DEFLATE,BIGTIFF=YES', overwrite=True)

#         # Clean up
#         g.remove(type='raster', name=f'merit_dem_{rgn}_tmp', flags='f')

#     # Create slope map [needed for PDM] 
#     try:
#         r.slope_aspect(elevation='merit_dem_globe_0.004167Deg', slope='merit_dem_slope_globe_0.004167Deg', format='degrees', overwrite=overwrite)
#     except grass.exceptions.CalledModuleError:
#         pass 

#     return 0
