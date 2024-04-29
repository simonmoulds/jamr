#!/usr/bin/env python
# -*- coding: utf-8 -*-

import netCDF4
from utils import *

def get_jules_frac(year, frac_type_names):
    ntype = len(frac_type_names)
    frac = []
    surf_hgt = []
    for lc_name in frac_type_names:
        # Fractional cover:
        frac_ds = rasterio.open(
            os.environ['LC_' + lc_name.upper() + '_' + str(year) + '_FN']
        )
        frac_map = frac_ds.read(1, masked=False).squeeze()
        frac.append(frac_map)
        # Mean surface height of land cover:
        surf_hgt_ds = rasterio.open(
            os.environ['LC_' + lc_name.upper() + '_' + str(year) + '_SURF_HGT_FN']
        )
        surf_hgt_map = surf_hgt_ds.read(1, masked=False).squeeze()
        surf_hgt.append(surf_hgt_map)

    # Divide by sum to ensure the fractions sum to one
    frac = np.stack(frac)
    frac /= frac.sum(axis=0)
    surf_hgt = np.stack(surf_hgt)

    # Compute weighted mean of all cells (for ice cells)
    mean_surf_hgt = (
        np.sum(surf_hgt * frac, axis=0)
        / np.sum(frac, axis=0)
    )
    
    # Compute weighted mean of soil and ice cells (for non-ice cells)
    soil_ice_sum = np.sum(frac[-2:, ...], axis=0)
    mean_surf_hgt_soil_ice = np.divide(
        np.sum(surf_hgt[-2:, ...] * frac[-2:, ...], axis=0),
        soil_ice_sum,
        out=np.zeros_like(soil_ice_sum),
        where=soil_ice_sum>0
    )
    # mean_surf_hgt_soil_ice = (
    #     np.sum(surf_hgt[-2:, ...] * frac[-2:, ...], axis=0)
    #     / np.sum(frac[-2:, ...], axis=0)
    # )

    # original ice/soil fractions
    ice_orig = frac[-1, ...]
    soil_orig = frac[-2, ...]

    ice = np.zeros_like(ice_orig).astype(np.bool)
    ice[ice_orig > 0.5] = True
    not_ice = np.logical_not(ice)

    # initially set all fractions/heights in ice gridboxes to zero
    frac *= not_ice[None, ...]
    surf_hgt *= not_ice[None, ...]
    # then set ice fraction to one
    frac[-1][ice] = 1
    frac[-1][not_ice] = 0
    # in non-ice gridboxes, add original ice fraction to bare soil
    frac[-2] = (soil_orig + ice_orig) * not_ice
    # surface height in ice grid boxes is the mean of all fractions
    surf_hgt[-1][ice] = mean_surf_hgt[ice]
    # surface height in non-ice is the weighted mean of bare soil
    # and original ice fraction
    surf_hgt[-2][not_ice] = mean_surf_hgt_soil_ice[not_ice]
    # divide by sum again, to ensure fractions continue to sum to one
    frac /= frac.sum(axis=0)
    frac = np.ma.array(
        frac,
        mask=np.broadcast_to(
            np.logical_not(LAND_FRAC),
            (ntype, NLAT, NLON)
        ),
        dtype=np.float64,
        fill_value=F8_FILLVAL
    )
    surf_hgt = np.ma.array(
        surf_hgt,
        mask=np.broadcast_to(
            np.logical_not(LAND_FRAC),
            (ntype, NLAT, NLON)
        ),
        dtype=np.float64,
        fill_value=F8_FILLVAL
    )
    return frac, surf_hgt

def write_jules_frac_2d(frac_fn, frac, var_name, var_units, x_dim_name, y_dim_name, type_dim_name):
    nco = netCDF4.Dataset(frac_fn, 'w', format='NETCDF4')
    ntype = frac.shape[0]
    nco = add_lat_lon_dims_2d(nco, x_dim_name, y_dim_name)

    nco.createDimension(type_dim_name, ntype)
    var = nco.createVariable(type_dim_name, 'i4', (type_dim_name,))
    var.units = '1'
    var.standard_name = type_dim_name
    var.long_name = type_dim_name
    var[:] = np.arange(1, ntype+1)
    
    var = nco.createVariable(
        var_name, 'f8', (type_dim_name, y_dim_name, x_dim_name),
        fill_value=F8_FILLVAL
    )
    var.units = var_units
    var.standard_name = var_name
    var.grid_mapping = 'latitude_longitude'
    var[:] = frac
    nco.close()

def write_jules_frac_ants(year, lc_names, frac_fn):
    frac, _ = get_jules_frac(year, lc_names)    
    ntype = frac.shape[0]
    # extract region characteristics, and move western
    # hemisphere east of east hemisphere.
    land_frac, lat_vals, lon_vals, extent = get_region_data()
    nlat = len(lat_vals)
    nlon = len(lon_vals)
    lat_bnds = get_lat_lon_bnds(lat_vals, (extent.top, extent.bottom))
    lon_bnds = get_lat_lon_bnds(lon_vals, (extent.left, extent.right))
    west_hemisphere = lon_vals < 0.
    east_hemisphere = ~west_hemisphere
    frac = np.concatenate([frac[:, :, east_hemisphere], frac[:, :, west_hemisphere]], axis=2)
    lon_vals = np.concatenate([lon_vals[east_hemisphere], lon_vals[west_hemisphere] + 360.], axis=0)
    lon_bnds = np.concatenate([lon_bnds[east_hemisphere, :], lon_bnds[west_hemisphere, :] + 360.], axis=0)
    # create file
    nco = netCDF4.Dataset(frac_fn, 'w', format='NETCDF4')
    nco.grid_staggering = 6
    
    # add dimensions
    nco.createDimension('dim0', ntype)
    nco.createDimension('latitude', nlat)
    nco.createDimension('longitude', nlon)
    nco.createDimension('bnds', 2)
    # add variables
    var = nco.createVariable(
        'longitude', 'f8', ('longitude',)
    )
    var.axis = 'X'
    var.bounds = 'longitude_bnds'
    var.units = 'degrees_east'
    var.standard_name = 'longitude'
    var[:] = lon_vals
    var = nco.createVariable(
        'longitude_bnds', 'f8', ('longitude', 'bnds')
    )
    var[:] = lon_bnds
    var = nco.createVariable(
        'latitude', 'f8', ('latitude',)
    )
    var.axis = 'Y'
    var.bounds = 'latitude_bnds'
    var.units = 'degrees_north'
    var.standard_name = 'latitude'
    var[:] = lat_vals
    var = nco.createVariable(
        'latitude_bnds', 'f8', ('latitude', 'bnds')
    )
    var[:] = lat_bnds
    var = nco.createVariable(
        'latitude_longitude', 'i4'
    )
    var.grid_mapping_name = 'latitude_longitude'
    var.longitude_of_prime_meridian = 0.
    var.earth_radius = 6371229.    
    # TODO: change variable name
    var = nco.createVariable(
        'land_cover_lccs', 'f8', ('dim0', 'latitude', 'longitude'),
        fill_value=F8_FILLVAL
    )
    var.units = '1'
    var.um_stash_source = 'm01s00i216'
    var.standard_name = 'land_cover_lccs'
    var.grid_mapping = 'latitude_longitude'
    var.coordinates = 'pseudo_level'
    var[:] = frac
        
    var = nco.createVariable('pseudo_level', 'i4', ('dim0',))
    var.units = '1'
    var.long_name = 'pseudo_level'
    var[:] = np.arange(1, ntype+1)
    nco.close()
    
def write_jules_frac_1d(frac_fn, frac, var_name, var_units, grid_dim_name, type_dim_name):
    nco = netCDF4.Dataset(frac_fn, 'w', format='NETCDF4')
    ntype, nland = frac.shape[0], frac.shape[1]
    nco.createDimension(grid_dim_name, nland)
    nco.createDimension(type_dim_name, ntype)

    var = nco.createVariable(type_dim_name, 'i4', (type_dim_name,))
    var.units = '1'
    var.standard_name = type_dim_name
    var.long_name = type_dim_name
    var[:] = np.arange(1, ntype+1)

    var = nco.createVariable(
        var_name, 'f8', (type_dim_name, grid_dim_name),
        fill_value=F8_FILLVAL
    )
    var.units = var_units
    var.standard_name = var_name
    var[:] = frac
    nco.close()

# def write_jules_frac(year, lc_names, frac_fn, surf_hgt_fn, one_d=False):
#     frac, surf_hgt = get_jules_frac(year, lc_names)    
#     ntype = frac.shape[0]
#     if one_d:
#         mask = LAND_FRAC > 0.
#         mask = mask[None, :, :] * np.ones(ntype)[:, None, None]
#         mask = mask.astype(bool)
#         frac = frac.transpose()[mask.transpose()]
#         surf_hgt = surf_hgt.transpose()[mask.transpose()]        
#         write_jules_frac_1d(frac_fn, frac, 'frac', '1')
#         write_jules_frac_1d(surf_hgt_fn, surf_hgt, 'elevation', 'm')
#     else:
#         write_jules_frac_2d(frac_fn, frac, 'frac', '1')
#         write_jules_frac_2d(surf_hgt_fn, surf_hgt, 'elevation', 'm')
