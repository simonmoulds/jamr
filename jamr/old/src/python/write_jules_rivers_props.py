#!/usr/bin/env python
# -*- coding: utf-8 -*-

import netCDF4
from utils import *


def write_jules_rivers_props_1d(routing_fn, routing_maps, grid_dim_name):
    
    nco = netCDF4.Dataset(routing_fn, 'w', format='NETCDF4')
    mask = LAND_FRAC > 0.
    nland = mask.sum()
    for key, value in routing_maps.items():
        routing_maps[key] = value.transpose()[mask.transpose()]
        
    nco.createDimension(grid_dim_name, nland)
    var = nco.createVariable(
        'area', 'i4', (grid_dim_name,), fill_value=I4_FILLVAL
    )
    var.units = '1'
    var.standard_name = 'area'
    var.long_name = 'area'
    var[:] = routing_maps['accum_cell']

    var = nco.createVariable(
        'direction', 'i4', (grid_dim_name,), fill_value=I4_FILLVAL
    )
    var.units = '1'
    var.standard_name = 'direction'
    var.long_name = 'direction'
    var[:] = routing_maps['draindir_trip']
    nco.close()


def write_jules_rivers_props_2d(routing_fn, routing_maps, x_dim_name, y_dim_name):

    nco = netCDF4.Dataset(routing_fn, 'w', format='NETCDF4')
    nco = add_lat_lon_dims_2d(nco, x_dim_name, y_dim_name)
    
    var = nco.createVariable(
        'area', 'i4', (y_dim_name, x_dim_name), fill_value=I4_FILLVAL
    )
    var.units = '1'
    var.standard_name = 'area'
    var.grid_mapping = 'latitude_longitude'
    var[:] = routing_maps['accum_cell']

    var = nco.createVariable(
        'direction', 'i4', (y_dim_name, x_dim_name), fill_value=I4_FILLVAL
    )
    var.units = '1'
    var.standard_name = 'direction'
    var.grid_mapping = 'latitude_longitude'
    var[:] = routing_maps['draindir_trip']
    nco.close()
            

# def write_jules_rivers_props(routing_fn, one_d=False):

#     # Read all river properties (area, direction)
#     accum_ds = rasterio.open(os.environ['ACCUM_FN'])
#     draindir_ds = rasterio.open(os.environ['DRAINDIR_FN'])
#     routing_maps = {}
#     routing_maps['accum_cell'] = accum_ds.read(1, masked=False).squeeze()
#     routing_maps['draindir_trip'] = draindir_ds.read(1, masked=False).squeeze()    
#     for var in routing_maps.keys():
#         arr = routing_maps[var]
#         arr = np.ma.masked_array(
#             arr,
#             mask=np.broadcast_to(
#                 np.logical_not(LAND_FRAC),
#                 arr.shape
#             ),
#             dtype=np.int32,
#             fill_value=I4_FILLVAL
#         )
#         routing_maps[var] = arr

#     # Write netCDF:
#     if one_d:
#         write_jules_rivers_props_1d(routing_fn, routing_maps)
#     else:
#         write_jules_rivers_props_2d(routing_fn, routing_maps)
