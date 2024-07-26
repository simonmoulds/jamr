
import os
import netCDF4
import rasterio
import numpy as np

from grass.script import array as garray 
from grass.script import core as grass 

F8_FILLVAL = netCDF4.default_fillvals['f8']
F4_FILLVAL = netCDF4.default_fillvals['f4']
I4_FILLVAL = netCDF4.default_fillvals['i4']


def raster2array(map):
    # with rasterio.open(fn) as src:
    #     transform = src.transform
    #     extent = src.bounds
    #     data = src.read(1, masked=False)
    
    data = garray.array(map)
    # data = data.squeeze()
    region = grass.region()
    x_vals = np.arange(region['cols']) * region['ewres'] + region['w'] + region['ewres'] / 2.
    y_vals = np.arange(region['rows']) * region['nsres'] + region['s'] + region['nsres'] / 2. 
    y_vals = y_vals[::-1] # north-south
    x_bnds = get_lat_lon_bnds(x_vals, (region['w'], region['e']))
    y_bnds = get_lat_lon_bnds(y_vals, (region['n'], region['s']))

    # ny = data.shape[0]
    # nx = data.shape[1]
    # x_vals = np.arange(nx) * transform[0] + transform[2] + transform[0]/2
    # y_vals = np.arange(ny) * transform[4] + transform[5] + transform[4]/2
    # x_bnds = get_lat_lon_bnds(x_vals, (extent.left, extent.right))
    # y_bnds = get_lat_lon_bnds(y_vals, (extent.top, extent.bottom))
    coords = (x_vals, y_vals)
    bnds = (x_bnds, y_bnds)
    return coords, bnds, data


def get_lat_lon_grids(lat_vals, lon_vals):
    """Expand latitude and longitude values to grid."""
    nlat = len(lat_vals)
    nlon = len(lon_vals)
    lon_vals_2d = lon_vals[None, :] * np.ones(nlat)[:, None]
    lat_vals_2d = lat_vals[:, None] * np.ones(nlon)[None, :]
    return lon_vals_2d, lat_vals_2d


def get_lat_lon_bnds(vals, extent):
    """Calculate lat/lon bounds."""
    bound = np.linspace(extent[0], extent[1], endpoint=True, num=len(vals)+1)
    bounds = np.array([bound[:-1], bound[1:]]).T
    return bounds


def add_lat_lon_dims_2d(nco, x_dim_name, y_dim_name, x_vals, y_vals, x_bnds, y_bnds):
    """Add 2d latitude/longitude data to a netCDF object."""    
    nco.createDimension(y_dim_name, len(y_vals))
    nco.createDimension(x_dim_name, len(x_vals))
    nco.createDimension('bnds', 2)

    # add x dims
    var = nco.createVariable(
        x_dim_name, 'f8', (x_dim_name,)
    )
    x_bnds_dim_name = x_dim_name + '_bnds'
    var.axis = 'X'
    var.bounds = x_bnds_dim_name
    var.units = 'degrees_east'
    var.standard_name = x_dim_name
    var[:] = x_vals
    # add x bounds
    var = nco.createVariable(
        x_bnds_dim_name, 'f8', (x_dim_name, 'bnds')
    )
    var[:] = x_bnds

    # add y dims
    var = nco.createVariable(
        y_dim_name, 'f8', (y_dim_name,)
    )
    y_bnds_dim_name = y_dim_name + '_bnds'
    var.axis = 'Y'
    var.bounds = y_bnds_dim_name
    var.units = 'degrees_north'
    var.standard_name = y_dim_name
    var[:] = y_vals

    # add y bounds
    var = nco.createVariable(
        y_bnds_dim_name, 'f8', (y_dim_name, 'bnds')
    )
    var[:] = y_bnds

    # add grid mapping
    var = nco.createVariable(
        'latitude_longitude', 'i4'
    )
    var.grid_mapping_name = 'latitude_longitude'
    var.longitude_of_prime_meridian = 0.
    var.earth_radius = 6371229.
    
    return nco

# def get_region_data():
#     """Function to obtain geospatial parameters."""
#     ds = rasterio.open(os.environ['JULES_LAND_FRAC_FN'])
#     land_frac = ds.read(1, masked=False).squeeze()  # squeeze to remove unit dimension
#     transform = ds.transform                        # affine
#     extent = ds.bounds
#     nlat = land_frac.shape[0]                       # nrow
#     nlon = land_frac.shape[1]                       # ncol
#     lon_vals = np.arange(nlon) * transform[0] + transform[2] + transform[0]/2
#     lat_vals = np.arange(nlat) * transform[4] + transform[5] + transform[4]/2
#     return land_frac, lat_vals, lon_vals, extent



# # Constants:
# LAND_FRAC, LAT_VALS, LON_VALS, EXTENT = get_region_data()
# NLAT = len(LAT_VALS)
# NLON = len(LON_VALS)
# LAT_BNDS = get_lat_lon_bnds(LAT_VALS, (EXTENT.top, EXTENT.bottom))
# LON_BNDS = get_lat_lon_bnds(LON_VALS, (EXTENT.left, EXTENT.right))

# def add_lat_lon_dims_2d(nco, x_dim_name, y_dim_name):
#     """Add 2d latitude/longitude data to a netCDF object."""    
#     nco.createDimension(y_dim_name, NLAT)
#     nco.createDimension(x_dim_name, NLON)
#     nco.createDimension('bnds', 2)
#     # add x dims
#     var = nco.createVariable(
#         x_dim_name, 'f8', (x_dim_name,)
#     )
#     x_bnds_dim_name = x_dim_name + '_bnds'
#     var.axis = 'X'
#     var.bounds = x_bnds_dim_name
#     var.units = 'degrees_east'
#     var.standard_name = x_dim_name
#     var[:] = LON_VALS
#     # add x bounds
#     var = nco.createVariable(
#         x_bnds_dim_name, 'f8', (x_dim_name, 'bnds')
#     )
#     var[:] = LON_BNDS
#     # add y dims
#     var = nco.createVariable(
#         y_dim_name, 'f8', (y_dim_name,)
#     )
#     y_bnds_dim_name = y_dim_name + '_bnds'
#     var.axis = 'Y'
#     var.bounds = y_bnds_dim_name
#     var.units = 'degrees_north'
#     var.standard_name = y_dim_name
#     var[:] = LAT_VALS
#     # add y bounds
#     var = nco.createVariable(
#         y_bnds_dim_name, 'f8', (y_dim_name, 'bnds')
#     )
#     var[:] = LAT_BNDS
#     # add grid mapping
#     var = nco.createVariable(
#         'latitude_longitude', 'i4'
#     )
#     var.grid_mapping_name = 'latitude_longitude'
#     var.longitude_of_prime_meridian = 0.
#     var.earth_radius = 6371229.
#     return nco
