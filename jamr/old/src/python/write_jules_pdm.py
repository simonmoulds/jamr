#!/usr/bin/env python
# -*- coding: utf-8 -*-

import netCDF4
from utils import *


def write_jules_pdm_1d(pdm_fn, slope, grid_dim_name):

    nco = netCDF4.Dataset(pdm_fn, 'w', format='NETCDF4')    
    mask = LAND_FRAC > 0.
    nland = mask.sum()
    slope = slope.transpose()[mask.transpose()]    
    nco.createDimension(grid_dim_name, nland)
    var = nco.createVariable(
        'slope', 'f8', (grid_dim_name,), fill_value=F8_FILLVAL
    )
    var.units = 'degrees'
    var.standard_name = 'slope'
    var.long_name = 'slope'
    var[:] = slope
    nco.close()

def write_jules_pdm_2d(pdm_fn, slope, x_dim_name, y_dim_name):

    nco = netCDF4.Dataset(pdm_fn, 'w', format='NETCDF4')
    nco = add_lat_lon_dims_2d(nco, x_dim_name, y_dim_name)
    var = nco.createVariable(
        'slope', 'f8', (y_dim_name, x_dim_name),
        fill_value=F8_FILLVAL
    )
    var.units = 'degrees'
    var.standard_name = 'slope'
    var.long_name = 'slope'
    var.grid_mapping = 'latitude_longitude'
    var[:] = slope
    nco.close()

# def write_jules_pdm(pdm_fn, one_d=False):
    
#     # Read PDM parameter (i.e. slope)
#     slope_ds = rasterio.open(os.environ['SLOPE_FN'])
#     slope = slope_ds.read(1, masked=False).squeeze()
#     slope = np.ma.masked_array(
#         slope,
#         mask=np.broadcast_to(
#             np.logical_not(LAND_FRAC),
#             slope.shape
#         ),
#         dtype=np.float64,
#         fill_value=F8_FILLVAL
#     )

#     # Write netCDF:
#     if one_d:
#         write_jules_pdm_1d(pdm_fn, slope)
#     else:
#         write_jules_pdm_2d(pdm_fn, slope)
