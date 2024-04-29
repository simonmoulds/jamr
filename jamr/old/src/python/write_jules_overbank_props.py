#!/usr/bin/env python
# -*- coding: utf-8 -*-

import netCDF4
from utils import *

def write_jules_overbank_props_1d(overbank_fn, overbank_maps, grid_dim_name):
    
    nco = netCDF4.Dataset(overbank_fn, 'w', format='NETCDF4')
    mask = LAND_FRAC > 0.
    nland = mask.sum()
    for key, value in overbank_maps.items():
        overbank_maps[key] = value.transpose()[mask.transpose()]        
    nco.createDimension(grid_dim_name, nland)
    var = nco.createVariable(
        'logn_mean', 'f8', (grid_dim_name,), fill_value=F8_FILLVAL
    )
    var.units = 'ln(m)'
    var.standard_name = 'logn_mean'
    var[:] = overbank_maps['logn_mean']
    
    var = nco.createVariable(
        'logn_stdev', 'f8', (grid_dim_name,), fill_value=F8_FILLVAL
    )
    var.units = 'ln(m)'
    var.standard_name = 'logn_stdev'
    var[:] = overbank_maps['logn_stdev']
    nco.close()

def write_jules_overbank_props_2d(overbank_fn, overbank_maps, x_dim_name, y_dim_name):
    
    nco = netCDF4.Dataset(overbank_fn, 'w', format='NETCDF4')
    nco = add_lat_lon_dims_2d(nco, x_dim_name, y_dim_name)    
    var = nco.createVariable(
        'logn_mean', 'f8', (y_dim_name, x_dim_name),
        fill_value=F8_FILLVAL
    )
    var.units = 'ln(m)'
    var.standard_name = 'logn_mean'
    var.grid_mapping = 'latitude_longitude'
    var[:] = overbank_maps['logn_mean']
    
    var = nco.createVariable(
        'logn_stdev', 'f8', (y_dim_name, x_dim_name),
        fill_value=F8_FILLVAL
    )
    var.units = 'ln(m)'
    var.standard_name = 'logn_stdev'
    var.grid_mapping = 'latitude_longitude'
    var[:] = overbank_maps['logn_stdev']
    nco.close()

# def write_jules_overbank_props(overbank_fn, one_d=False):
    
#     # Read overbank properties:
#     logn_mean_ds = rasterio.open(os.environ['LOGN_MEAN_FN'])
#     logn_stdev_ds = rasterio.open(os.environ['LOGN_STDEV_FN'])
#     overbank_maps = {}
#     overbank_maps['logn_mean'] = logn_mean_ds.read(1, masked=False).squeeze()
#     overbank_maps['logn_stdev'] = logn_stdev_ds.read(1, masked=False).squeeze()
#     for var in overbank_maps.keys():
#         arr = overbank_maps[var]
#         arr = np.ma.masked_array(
#             arr,
#             mask=np.broadcast_to(
#                 np.logical_not(LAND_FRAC),
#                 arr.shape
#             ),
#             dtype=np.float64,
#             fill_value=F8_FILLVAL
#         )
#         overbank_maps[var] = arr

#     # Write netCDF:
#     if one_d:
#         write_jules_overbank_props_1d(overbank_fn, overbank_maps)
#     else:
#         write_jules_overbank_props_2d(overbank_fn, overbank_maps)
