#!/usr/bin/env python
# -*- coding: utf-8 -*-

import netCDF4
from utils import *

def write_jules_latlon_1d(latlon_fn, grid_dim_name):
    nco = netCDF4.Dataset(latlon_fn, 'w', format='NETCDF4')
    mask = LAND_FRAC > 0.
    lon_vals_2d, lat_vals_2d = get_lat_lon_grids(LAT_VALS, LON_VALS)
    lon_vals_1d = lon_vals_2d.transpose()[mask.transpose()]
    lat_vals_1d = lat_vals_2d.transpose()[mask.transpose()]
    nland = mask.sum()
    nco.createDimension(grid_dim_name, nland)
    
    var = nco.createVariable('longitude', 'f8', (grid_dim_name,))
    var.units = 'degrees_east'
    var.standard_name = 'longitude'
    var[:] = lon_vals_1d

    var = nco.createVariable('latitude', 'f8', (grid_dim_name,))
    var.units = 'degrees_east'
    var.standard_name = 'latitude'
    var[:] = lat_vals_1d
    nco.close()
    
def write_jules_latlon_2d(latlon_fn, x_dim_name, y_dim_name):
    nco = netCDF4.Dataset(latlon_fn, 'w', format='NETCDF4')
    nco = add_lat_lon_dims_2d(nco, x_dim_name, y_dim_name)
    lon_vals_2d, lat_vals_2d = get_lat_lon_grids(
        LAT_VALS, LON_VALS
    )
    var = nco.createVariable(
        'longitude', 'f8', (y_dim_name, x_dim_name)
    )
    var.units = 'degrees_east'
    var.standard_name = 'longitude'
    var[:] = lon_vals_2d
    var = nco.createVariable(
        'latitude', 'f8', (y_dim_name, x_dim_name)
    )
    var.units = 'degrees_east'
    var.standard_name = 'latitude'
    var[:] = lat_vals_2d
    nco.close()

# def write_jules_latlon(latlon_fn, one_d=False):
#     if one_d:
#         write_jules_latlon_1d(latlon_fn)
#     else:
#         write_jules_latlon_2d(latlon_fn)
