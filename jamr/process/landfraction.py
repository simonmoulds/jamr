#!/usr/bin/env python3

import os
import re
import glob
import time
import logging
import rasterio 
import numpy as np
import netCDF4
import grass.script as gscript

LOGGER = logging.getLogger(__name__)

from jamr.process.ancillarydataset import AncillaryDataset
from jamr.utils.grass_utils import (grass_remove_mask, grass_map_exists, grass_remove_tmp)
from jamr.utils.utils import (get_lat_lon_grids, add_lat_lon_dims_2d, raster2array)
from jamr.utils.constants import I4_FILLVAL


class LandFractionFactory:
    @staticmethod
    def create_land_fraction(method,
                             config,
                             inputdata,
                             overwrite):
        if method == 'ESA':
            return ESALandFraction(config, inputdata, overwrite) 
        else:
            raise ValueError(f'Unknown land fraction method: {method}')


class ESALandFraction(AncillaryDataset):
    def __init__(self, 
                 config, 
                 inputdata,
                 overwrite):

        self.config = config 
        self.inputdata = inputdata
        self.overwrite = overwrite
        self.region_name = config['region']['name']
        grass_remove_mask()
        self._set_mapnames() 

    def _set_mapnames(self): 
        self.mapname_native = f'esacci_landfrac_{self.region_name}_native'
        self.mapname = f'esacci_landfrac_{self.region_name}'

    def compute(self):
        self._set_native_region(self.inputdata.landcover.mapnames[2015])

        # Resample waterbodies map to the landcover map resolution
        if not grass_map_exists('raster', self.mapname_native, 'PERMANENT') or self.overwrite:
            # LOGGER.info(f'Resampling water bodies map to resolution of land cover maps')
            p = gscript.start_command(
                'r.resamp.stats', 
                input=self.inputdata.waterbodies.mapnames[-1],
                output='water_bodies_min_tmp',
                method='minimum',
                overwrite=self.overwrite, 
            )
            p.communicate()

            # LOGGER.info(f'Identifying ocean grid cells from water bodies map')
            p = gscript.start_command(
                'r.mapcalc', 
                expression='ocean_min_tmp = if(water_bodies_min_tmp == 0, 1, 0)', 
                overwrite=self.overwrite, 
            )
            p.communicate()
            # stdout, stderr = p.communicate()

            # LOGGER.info(f'Identifying water cells from reference land cover map')
            esaccilc_ref_map = self.inputdata.landcover[2015]
            p = gscript.start_command(
                'r.mapcalc', 
                expression=f'esacci_lc_water_tmp = if({esaccilc_ref_map} == 210, 1, 0)', 
                overwrite=self.overwrite, 
            )
            p.communicate()
            
            # LOGGER.info(f'Identifying ocean grid cells as union of water bodies map and land cover map')
            p = gscript.start_command(
                'r.mapcalc', 
                expression=f'ocean_tmp = if((ocean_min_tmp==1 && esacci_lc_water_tmp==1), 1, 0)', 
                overwrite=self.overwrite, 
            )
            p.communicate()

            p = gscript.start_command(
                'r.mapcalc', 
                expression=f'{self.mapname_native} = 1 - ocean_tmp', 
                overwrite=self.overwrite, 
            )
            p.communicate()

        # Resample to target resolution
        self._set_target_region()
        self._resample(input_map=self.mapname_native, output_map=self.mapname, method='average')

        # Remove temporary maps
        grass_remove_tmp()

    def write_netcdf(self):
        output_filename = os.path.join(self.config['main']['output_directory'], 'jamr_landfrac.nc')
        # write_jules_land_frac_1d(input, output, 'land')
        write_jules_land_frac_2d(self.mapname, output_filename, 'x', 'y')


def write_jules_land_frac_1d(input, output, grid_dim_name):

    coords, _, land_frac = raster2array(input)

    nco = netCDF4.Dataset(output, 'w', format='NETCDF4')
    mask = land_frac > 0.
    lon_vals_2d, lat_vals_2d = get_lat_lon_grids(coords[1], coords[0])
    lon_vals_1d = lon_vals_2d.transpose()[mask.transpose()]
    lat_vals_1d = lat_vals_2d.transpose()[mask.transpose()]
    nland = mask.sum()
    nco.createDimension(grid_dim_name, nland)

    var = nco.createVariable('longitude', 'f8', (grid_dim_name,))
    var.units = 'degrees_east'
    var.standard_name = 'longitude'
    var[:] = lon_vals_1d

    var = nco.createVariable('latitude', 'f8', (grid_dim_name,))
    var.units = 'degrees_north'
    var.standard_name = 'latitude'
    var[:] = lat_vals_1d

    var = nco.createVariable(
        'land_frac', 'i4', (grid_dim_name,),
        fill_value=I4_FILLVAL
    )
    var.units = '1'
    var.standard_name = 'land_frac'
    var[:] = land_frac.transpose()[mask.transpose()]
    nco.close()
    return None


def write_jules_land_frac_2d(input, output, x_dim_name, y_dim_name):
    coords, bnds, land_frac = raster2array(input)
    nco = netCDF4.Dataset(output, 'w', format='NETCDF4')
    nco = add_lat_lon_dims_2d(nco, x_dim_name, y_dim_name, coords[0], coords[1], bnds[0], bnds[1])
    var = nco.createVariable(
        'land_frac', 'i4', (y_dim_name, x_dim_name),
        fill_value=I4_FILLVAL
    )
    var.units = '1'
    var.standard_name = 'land_frac'
    var.grid_mapping = 'latitude_longitude'
    var[:] = land_frac
    nco.close()
