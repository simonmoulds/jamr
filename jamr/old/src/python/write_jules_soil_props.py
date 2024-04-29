#!/usr/bin/env python
# -*- coding: utf-8 -*-

import netCDF4
from scipy.interpolate import interp1d
from utils import *

# depths of SoilGrids data
NATIVE_DEPTHS = np.array([0., 0.05, 0.15, 0.30, 0.60, 1., 2.])
TARGET_DEPTHS = np.array([0.1, 0.35, 1., 3.])
N_LAYER = TARGET_DEPTHS.shape[0]
N_HORIZON = NATIVE_DEPTHS.shape[0]

def aggregate_soil_data(x):
    """Interpolate soil data from native vertical
    resolution to target resolution.
    """
    # ensure that the target depth array starts at zero
    target_depths_zero = np.sort(
        np.unique(
            np.insert(TARGET_DEPTHS, 0, np.array([0.]))
        )
    )
    all_depths = np.sort(
        np.unique(
            np.concatenate((NATIVE_DEPTHS, target_depths_zero))
        )
    )
    interp_fun = interp1d(
        NATIVE_DEPTHS,
        x,
        axis=0,
        bounds_error=False,
        fill_value=(x[0, ...], x[-1, ...])
    )
    x = interp_fun(all_depths)
    x_new = []
    for i in range(len(target_depths_zero) - 1):
        layer_index = (
            (all_depths <= target_depths_zero[i + 1])
            & (all_depths >= target_depths_zero[i])
        )
        max_depth = np.max(all_depths[layer_index])
        min_depth = np.min(all_depths[layer_index])
        x_new.append(
            np.trapz(
                x[layer_index, ...],
                all_depths[layer_index],
                axis=0
            ) / (max_depth - min_depth)
        )
    x_new = np.stack(x_new)
    return x_new


def get_soil_data(varname, method, masked=True):
    """Function to read soil data."""
    array_list = []
    horizons = range(1, N_HORIZON + 1)
    for horizon in horizons:
        ds_name = \
            'SOIL_' + varname.upper() + '_' + method.upper() \
            + '_SL' + str(horizon) + '_FN'
        ds = rasterio.open(os.environ[ds_name])
        arr = ds.read(1, masked=masked).squeeze()
        array_list.append(arr)
    array = np.stack(array_list)
    array = aggregate_soil_data(array)
    return array


def get_soil_data_dict(method, masked=True):
    """Function to read soil data from file."""
    soil_data = {}
    albedo_ds = rasterio.open(os.environ['ALBEDO_FN'])
    soil_data['albsoil'] = albedo_ds.read(1, masked=masked).squeeze()
    soil_varnames = [
        'b', 'hcap', 'hcon', 'k_sat', 'psi_m',
        'theta_crit', 'theta_sat', 'theta_wilt'
    ]
    for varname in soil_varnames:
        soil_data[varname] = get_soil_data(
            varname,
            method,
            masked
        )
    return soil_data


def write_jules_soil_props_1d(soil_fn, soil_data, grid_dim_name, soil_dim_name):

    # Mask all soil data using land fraction data
    mask = LAND_FRAC > 0.
    nland = mask.sum()
    mask_3d = mask[None, :, :] * np.ones(N_LAYER)[:, None, None]
    mask_3d = mask_3d.astype(bool)
    for key, value in soil_data:
        soil_data[key] = value.transpose()[mask_3d.transpose()]
        
    nco = netCDF4.Dataset(soil_fn, 'w', format='NETCDF4')
    nco.createDimension(grid_dim_name, nland)
    nco.createDimension(soil_dim_name, N_LAYER)
        
    var = nco.createVariable(soil_dim_name, 'i4', (soil_dim_name))
    var.units = '1'
    var.standard_name = soil_dim_name
    var.long_name = soil_dim_name
    var[:] = np.arange(1, (N_LAYER + 1))

    # PP code: 1395
    var = nco.createVariable(
        'albsoil', 'f8', (grid_dim_name,), fill_value=F8_FILLVAL
    )
    var.units = '1'
    var.standard_name = 'albsoil'
    var.long_name = 'soil albedo'
    var[:] = soil_data['albsoil']

    # PP code: 1381
    var = nco.createVariable(
        'b', 'f8', (soil_dim_name, grid_dim_name), fill_value=F8_FILLVAL
    )
    var.units = '1'
    var.standard_name = 'b'
    var.long_name = 'exponent in soil hydraulic characteristics'
    var[:] = soil_data['b']

    # PP code: 335
    var = nco.createVariable(
        'hcap', 'f8', (soil_dim_name, grid_dim_name), fill_value=F8_FILLVAL
    )
    var.units = 'J m-3 K-1'
    var.standard_name = 'hcap'
    var.long_name = 'dry heat capacity'
    var[:] = soil_data['hcap']

    # PP code: 336
    var = nco.createVariable(
        'hcon', 'f8', (soil_dim_name, grid_dim_name), fill_value=F8_FILLVAL
    )
    var.units = 'W m-1 K-1'
    var.standard_name = 'hcon'
    var.long_name = 'dry thermal conductivity'
    var[:] = soil_data['hcon']

    # PP code: 333
    var = nco.createVariable(
        'satcon', 'f8', (soil_dim_name, grid_dim_name), fill_value=F8_FILLVAL
    )
    var.units = 'kg m-2 s-1'
    var.standard_name = 'satcon'
    var.long_name = 'hydraulic conductivity at saturation'
    var[:] = soil_data['k_sat']

    # If l_vg_soil = TRUE (i.e. using van Genuchten model),
    # sathh = 1/alpha, where alpha is a parameter of the
    # van Genuchten model. Otherwise if l_vg_soil = FALSE
    # (i.e. using Brooks and Corey model), sathh is the
    # *absolute* value of the soil matric suction at
    # saturation (m). Morel-Seytoux et al. (1996) proposed
    # parameter equivalence such that alpha = pg/-psi_e, which
    # essentially means that the same sathh can be used for
    # l_vg_soil=True OR False
    
    # PP code: 342
    var = nco.createVariable(
        'sathh', 'f8', (soil_dim_name, grid_dim_name), fill_value=F8_FILLVAL
    )
    var.units = 'm'
    var.standard_name = 'sathh'
    var.long_name = 'absolute value of the soil matric suction at saturation'
    var[:] = soil_data['psi_m']

    # PP code: 330
    var = nco.createVariable(
        'sm_crit', 'f8', (soil_dim_name, grid_dim_name), fill_value=F8_FILLVAL
    )
    var.units = 'm3 m-3'
    var.standard_name = 'sm_crit'
    var.long_name = 'volumetric soil moisture content at critical point'
    var[:] = soil_data['theta_crit']

    # PP code: 332
    var = nco.createVariable(
        'sm_sat', 'f8', (soil_dim_name, grid_dim_name), fill_value=F8_FILLVAL
    )
    var.units = 'm3 m-3'
    var.standard_name = 'sm_sat'
    var.long_name = 'volumetric soil moisture content at saturation'
    var[:] = soil_data['theta_sat']

    # PP code: 329
    var = nco.createVariable(
        'sm_wilt', 'f8', (soil_dim_name, grid_dim_name), fill_value=F8_FILLVAL
    )
    var.units = 'm3 m-3'
    var.standard_name = 'sm_wilt'
    var.long_name = 'volumetric soil moisture content at wilting point'
    var[:] = soil_data['theta_wilt']
    nco.close()


def write_jules_soil_props_2d(soil_fn, soil_data, x_dim_name, y_dim_name, soil_dim_name):

    nco = netCDF4.Dataset(soil_fn, 'w', format='NETCDF4')
    nco = add_lat_lon_dims_2d(nco, x_dim_name, y_dim_name)
    
    nco.createDimension(soil_dim_name, N_LAYER)
    var = nco.createVariable(soil_dim_name, 'i4', (soil_dim_name))
    var.units = '1'
    var.standard_name = soil_dim_name
    var.long_name = soil_dim_name
    var[:] = np.arange(1, (N_LAYER + 1))

    # PP code: 1395
    var = nco.createVariable(
        'albsoil', 'f8', (y_dim_name, x_dim_name),
        fill_value=F8_FILLVAL
    )
    var.units = '1'
    var.standard_name = 'albsoil'
    var.long_name = 'soil albedo'
    var.grid_mapping = 'latitude_longitude'
    var[:] = soil_data['albsoil']

    # PP code: 1381
    var = nco.createVariable(
        'b', 'f8', (soil_dim_name, y_dim_name, x_dim_name),
        fill_value=F8_FILLVAL
    )
    var.units = '1'
    var.standard_name = 'b'
    var.long_name = 'exponent in soil hydraulic characteristics'
    var.grid_mapping = 'latitude_longitude'
    var[:] = soil_data['b']

    # PP code: 335
    var = nco.createVariable(
        'hcap', 'f8', (soil_dim_name, y_dim_name, x_dim_name),
        fill_value=F8_FILLVAL
    )
    var.units = 'J m-3 K-1'
    var.standard_name = 'hcap'
    var.long_name = 'dry heat capacity'
    var.grid_mapping = 'latitude_longitude'
    var[:] = soil_data['hcap']

    # PP code: 336
    var = nco.createVariable(
        'hcon', 'f8', (soil_dim_name, y_dim_name, x_dim_name),
        fill_value=F8_FILLVAL
    )
    var.units = 'W m-1 K-1'
    var.standard_name = 'hcon'
    var.long_name = 'dry thermal conductivity'
    var.grid_mapping = 'latitude_longitude'
    var[:] = soil_data['hcon']

    # PP code: 333
    var = nco.createVariable(
        'satcon', 'f8', (soil_dim_name, y_dim_name, x_dim_name),
        fill_value=F8_FILLVAL
    )
    var.units = 'kg m-2 s-1'
    var.standard_name = 'satcon'
    var.long_name = 'hydraulic conductivity at saturation'
    var.grid_mapping = 'latitude_longitude'
    var[:] = soil_data['k_sat']

    # If l_vg_soil = TRUE (i.e. using van Genuchten model),
    # sathh = 1/alpha, where alpha is a parameter of the
    # van Genuchten model. Otherwise if l_vg_soil = FALSE
    # (i.e. using Brooks and Corey model), sathh is the
    # *absolute* value of the soil matric suction at
    # saturation (m). Morel-Seytoux et al. (1996) proposed
    # parameter equivalence such that alpha = pg/-psi_e, which
    # essentially means that the same sathh can be used for
    # l_vg_soil=True OR False
    
    # PP code: 342
    var = nco.createVariable(
        'sathh', 'f8', (soil_dim_name, y_dim_name, x_dim_name),
        fill_value=F8_FILLVAL
    )
    var.units = 'm'
    var.standard_name = 'sathh'
    var.long_name = 'absolute value of the soil matric suction at saturation'
    var.grid_mapping = 'latitude_longitude'
    var[:] = soil_data['psi_m']

    # PP code: 330
    var = nco.createVariable(
        'sm_crit', 'f8', (soil_dim_name, y_dim_name, x_dim_name),
        fill_value=F8_FILLVAL
    )
    var.units = 'm3 m-3'
    var.standard_name = 'sm_crit'
    var.long_name = 'volumetric soil moisture content at critical point'
    var.grid_mapping = 'latitude_longitude'
    var[:] = soil_data['theta_crit']

    # PP code: 332
    var = nco.createVariable(
        'sm_sat', 'f8', (soil_dim_name, y_dim_name, x_dim_name),
        fill_value=F8_FILLVAL
    )
    var.units = 'm3 m-3'
    var.standard_name = 'sm_sat'
    var.long_name = 'volumetric soil moisture content at saturation'
    var.grid_mapping = 'latitude_longitude'
    var[:] = soil_data['theta_sat']

    # PP code: 329
    var = nco.createVariable(
        'sm_wilt', 'f8', (soil_dim_name, y_dim_name, x_dim_name),
        fill_value=F8_FILLVAL
    )
    var.units = 'm3 m-3'
    var.standard_name = 'sm_wilt'
    var.long_name = 'volumetric soil moisture content at wilting point'
    var.grid_mapping = 'latitude_longitude'
    var[:] = soil_data['theta_wilt']
    nco.close()

# def write_jules_soil_props(year, method, ice_frac, soil_fn, one_d=False):

#     # Load soil data and apply mask to all variables:
#     soil_data = get_soil_data_dict(method, masked=False)
#     for key in soil_data:
#         soil_data[key] = np.ma.array(
#             data=soil_data[key],
#             mask=np.broadcast_to(
#                 np.logical_not(LAND_FRAC),
#                 soil_data[key].shape
#             ),
#             dtype=np.float64,
#             fill_value=F8_FILLVAL
#         )

#     # Set theta_sat in ice gridboxes to zero:
#     # http://jules-lsm.github.io/latest/namelists/ancillaries.nml.html#namelist-JULES_FRAC
#     th_s = soil_data['theta_sat'].copy()
#     ice_frac = np.broadcast_to(ice_frac[None, ...], th_s.shape)
#     th_s[ice_frac] = 0
#     soil_data['theta_sat'] = th_s

#     # Write netCDF files:
#     if one_d:
#         write_jules_soil_props_1d(soil_fn, soil_data)
#     else:
#         write_jules_soil_props_2d(soil_fn, soil_data)

