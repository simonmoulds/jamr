#!/usr/bin/env python
# -*- coding: utf-8 -*-

import netCDF4
from utils import *


def write_jules_top_1d(topmodel_fn, topmodel_maps, grid_dim_name):
    
    nco = netCDF4.Dataset(topmodel_fn, 'w', format='NETCDF4')    
    mask = LAND_FRAC > 0.
    nland = mask.sum()
    for key, value in topmodel_maps.items():
        topmodel_maps[key] = value.transpose()[mask.transpose()]
        
    nco.createDimension(grid_dim_name, nland)
    var = nco.createVariable(
        'fexp', 'f8', (grid_dim_name,), fill_value=F8_FILLVAL
    )
    var.units = '1'
    var.standard_name = 'fexp'
    var.long_name = 'fexp'
    var[:] = topmodel_maps['fexp']

    var = nco.createVariable(
        'ti_mean', 'f8', (grid_dim_name,),
        fill_value=F8_FILLVAL
    )
    var.units = '1'
    var.standard_name = 'ti_mean'
    var.long_name = 'ti_mean'
    var[:] = topmodel_maps['topidx_mean']

    var = nco.createVariable(
        'ti_stdev', 'f8', (grid_dim_name,),
        fill_value=F8_FILLVAL
    )
    var.units = '1'
    var.standard_name = 'ti_stdev'
    var.long_name = 'ti_stdev'
    var[:] = topmodel_maps['topidx_stdev']
    nco.close()

def write_jules_top_2d(topmodel_fn, topmodel_maps, x_dim_name, y_dim_name):
    nco = netCDF4.Dataset(topmodel_fn, 'w', format='NETCDF4')
    nco = add_lat_lon_dims_2d(nco, x_dim_name, y_dim_name)
    var = nco.createVariable(
        'fexp', 'f8', (y_dim_name, x_dim_name), fill_value=F8_FILLVAL
    )
    var.units = '1'
    var.standard_name = 'fexp'
    var.grid_mapping = 'latitude_longitude'
    var[:] = topmodel_maps['fexp']
    var = nco.createVariable(
        'ti_mean', 'f8', (y_dim_name, x_dim_name),
        fill_value=F8_FILLVAL
    )
    var.units = '1'
    var.standard_name = 'ti_mean'
    var.grid_mapping = 'latitude_longitude'
    var[:] = topmodel_maps['topidx_mean']
    var = nco.createVariable(
        'ti_stdev', 'f8', (y_dim_name, x_dim_name),
        fill_value=F8_FILLVAL
    )
    var.units = '1'
    var.standard_name = 'ti_stdev'
    var.grid_mapping = 'latitude_longitude'
    var[:] = topmodel_maps['topidx_stdev']
    nco.close()

# def write_jules_top(topmodel_fn, one_d=False):

#     # Read all TOPMODEL parameters
#     fexp_ds = rasterio.open(os.environ['FEXP_FN'])
#     topidx_mean_ds = rasterio.open(os.environ['HYDRO_TI_MEAN_FN'])  # TEMPORARY
#     topidx_stdev_ds = rasterio.open(os.environ['HYDRO_TI_SIG_FN'])  # TEMPORARY
#     topmodel_maps = {}
#     topmodel_maps['fexp'] = fexp_ds.read(1, masked=False).squeeze()
#     topmodel_maps['topidx_mean'] = topidx_mean_ds.read(1, masked=False).squeeze()
#     topmodel_maps['topidx_stdev'] = topidx_stdev_ds.read(1, masked=False).squeeze()
#     for var in topmodel_maps.keys():
#         arr = topmodel_maps[var]
#         arr = np.ma.masked_array(
#             arr,
#             mask=np.broadcast_to(
#                 np.logical_not(LAND_FRAC),
#                 arr.shape
#             ),
#             dtype=np.float64,
#             fill_value=F8_FILLVAL
#         )
#         topmodel_maps[var] = arr

#     # Write netCDF:
#     if one_d:
#         write_jules_top_1d(topmodel_fn, topmodel_maps)
#     else:
#         write_jules_top_2d(topmodel_fn, topmodel_maps)
