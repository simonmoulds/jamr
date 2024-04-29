#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import click
import numpy as np
import netCDF4

from write_jules_frac import get_jules_frac, write_jules_frac_1d, write_jules_frac_2d, write_jules_frac_ants
from write_jules_land_frac import write_jules_land_frac_1d, write_jules_land_frac_2d
from write_jules_latlon import write_jules_latlon_1d, write_jules_latlon_2d
from write_jules_overbank_props import write_jules_overbank_props_1d, write_jules_overbank_props_2d
from write_jules_pdm import write_jules_pdm_1d, write_jules_pdm_2d
from write_jules_rivers_props import write_jules_rivers_props_1d, write_jules_rivers_props_2d
from write_jules_soil_props import get_soil_data_dict, write_jules_soil_props_1d, write_jules_soil_props_2d
from write_jules_top import write_jules_top_1d, write_jules_top_2d
from utils import *

# Read environment variables from parent
ONE_D = bool(int(os.environ['ONE_D']))
GRID_DIM_NAME = str(os.environ['GRID_DIM_NAME'])
X_DIM_NAME = str(os.environ['X_DIM_NAME'])
Y_DIM_NAME = str(os.environ['Y_DIM_NAME'])
TIME_DIM_NAME = str(os.environ['TIME_DIM_NAME'])
PFT_DIM_NAME = str(os.environ['PFT_DIM_NAME'])
TYPE_DIM_NAME = str(os.environ['TYPE_DIM_NAME'])
TILE_DIM_NAME = str(os.environ['TILE_DIM_NAME'])
SOIL_DIM_NAME = str(os.environ['SOIL_DIM_NAME'])
SNOW_DIM_NAME = str(os.environ['SNOW_DIM_NAME'])
PDM = bool(int(os.environ['PDM']))
TOPMODEL = bool(int(os.environ['TOPMODEL']))
ROUTING = bool(int(os.environ['ROUTING']))
OVERBANK = bool(int(os.environ['OVERBANK']))
NINEPFT = bool(int(os.environ['NINEPFT']))
FIVEPFT = bool(int(os.environ['FIVEPFT']))
ANTSFORMAT = bool(int(os.environ['ANTSFORMAT']))
LAND_FRAC = bool(int(os.environ['LAND_FRAC']))
LATLON = bool(int(os.environ['LATLON']))
COSBY = bool(int(os.environ['COSBY']))
TOMAS = bool(int(os.environ['TOMASELLA']))
ROSETTA = bool(int(os.environ['ROSETTA']))
REGION = str(os.environ['REGION'])
PRODUCT = str(os.environ['PRODUCT'])
OUTDIR = str(os.environ['OUTDIR'])

# names of JULES land cover types
LC_NAMES_5PFT = [
    'tree_broadleaf', 'tree_needleleaf',
    'shrub', 'c4_grass', 'c3_grass',
    'urban', 'water', 'bare_soil', 'snow_ice'
]
LC_NAMES_9PFT = [
    'tree_broadleaf_evergreen_tropical',
    'tree_broadleaf_evergreen_temperate',
    'tree_broadleaf_deciduous',
    'tree_needleleaf_evergreen',
    'tree_needleleaf_deciduous', 'shrub_evergreen',
    'shrub_deciduous', 'c4_grass', 'c3_grass',
    'urban', 'water', 'bare_soil', 'snow_ice'
]

def write_jules_frac(year, lc_names, frac_fn, surf_hgt_fn):
    frac, surf_hgt = get_jules_frac(year, lc_names)
    ntype = frac.shape[0]
    if ONE_D:
        mask = LAND_FRAC > 0.
        mask = mask[None, :, :] * np.ones(ntype)[:, None, None]
        mask = mask.astype(bool)
        frac = frac.transpose()[mask.transpose()]
        surf_hgt = surf_hgt.transpose()[mask.transpose()]        
        write_jules_frac_1d(frac_fn, frac, 'frac', '1', GRID_DIM_NAME, TYPE_DIM_NAME)
        write_jules_frac_1d(surf_hgt_fn, surf_hgt, 'elevation', 'm', GRID_DIM_NAME, TYPE_DIM_NAME)
    else:
        write_jules_frac_2d(frac_fn, frac, 'frac', '1', X_DIM_NAME, Y_DIM_NAME, TYPE_DIM_NAME)
        write_jules_frac_2d(surf_hgt_fn, surf_hgt, 'elevation', 'm', X_DIM_NAME, Y_DIM_NAME, TYPE_DIM_NAME)

def write_jules_soil_props(year, method, ice_frac, soil_fn):
    # Load soil data and apply mask to all variables:
    soil_data = get_soil_data_dict(method, masked=False)
    for key in soil_data:
        soil_data[key] = np.ma.array(
            data=soil_data[key],
            mask=np.broadcast_to(
                np.logical_not(LAND_FRAC),
                soil_data[key].shape
            ),
            dtype=np.float64,
            fill_value=F8_FILLVAL
        )
    # Set theta_sat in ice gridboxes to zero:
    # http://jules-lsm.github.io/latest/namelists/ancillaries.nml.html#namelist-JULES_FRAC
    th_s = soil_data['theta_sat'].copy()
    ice_frac = np.broadcast_to(ice_frac[None, ...], th_s.shape)
    th_s[ice_frac] = 0
    soil_data['theta_sat'] = th_s
    # Write netCDF files:
    if ONE_D:
        write_jules_soil_props_1d(soil_fn, soil_data, GRID_DIM_NAME, SOIL_DIM_NAME)
    else:
        write_jules_soil_props_2d(soil_fn, soil_data, X_DIM_NAME, Y_DIM_NAME, SOIL_DIM_NAME)

def write_jules_overbank_props(overbank_fn):
    logn_mean_ds = rasterio.open(os.environ['LOGN_MEAN_FN'])
    logn_stdev_ds = rasterio.open(os.environ['LOGN_STDEV_FN'])
    overbank_maps = {}
    overbank_maps['logn_mean'] = logn_mean_ds.read(1, masked=False).squeeze()
    overbank_maps['logn_stdev'] = logn_stdev_ds.read(1, masked=False).squeeze()
    for var in overbank_maps.keys():
        arr = overbank_maps[var]
        arr = np.ma.masked_array(
            arr,
            mask=np.broadcast_to(
                np.logical_not(LAND_FRAC),
                arr.shape
            ),
            dtype=np.float64,
            fill_value=F8_FILLVAL
        )
        overbank_maps[var] = arr
    if ONE_D:
        write_jules_overbank_props_1d(overbank_fn, overbank_maps, GRID_DIM_NAME)
    else:
        write_jules_overbank_props_2d(overbank_fn, overbank_maps, X_DIM_NAME, Y_DIM_NAME)

def write_jules_pdm(pdm_fn):
    slope_ds = rasterio.open(os.environ['SLOPE_FN'])
    slope = slope_ds.read(1, masked=False).squeeze()
    slope = np.ma.masked_array(
        slope,
        mask=np.broadcast_to(
            np.logical_not(LAND_FRAC),
            slope.shape
        ),
        dtype=np.float64,
        fill_value=F8_FILLVAL
    )
    if ONE_D:
        write_jules_pdm_1d(pdm_fn, slope, GRID_DIM_NAME)
    else:
        write_jules_pdm_2d(pdm_fn, slope, X_DIM_NAME, Y_DIM_NAME)

def write_jules_top(topmodel_fn):
    fexp_ds = rasterio.open(os.environ['FEXP_FN'])
    topidx_mean_ds = rasterio.open(os.environ['HYDRO_TI_MEAN_FN'])  # TEMPORARY
    topidx_stdev_ds = rasterio.open(os.environ['HYDRO_TI_SIG_FN'])  # TEMPORARY
    topmodel_maps = {}
    topmodel_maps['fexp'] = fexp_ds.read(1, masked=False).squeeze()
    topmodel_maps['topidx_mean'] = topidx_mean_ds.read(1, masked=False).squeeze()
    topmodel_maps['topidx_stdev'] = topidx_stdev_ds.read(1, masked=False).squeeze()
    for var in topmodel_maps.keys():
        arr = topmodel_maps[var]
        arr = np.ma.masked_array(
            arr,
            mask=np.broadcast_to(
                np.logical_not(LAND_FRAC),
                arr.shape
            ),
            dtype=np.float64,
            fill_value=F8_FILLVAL
        )
        topmodel_maps[var] = arr
    if ONE_D:
        write_jules_top_1d(topmodel_fn, topmodel_maps, GRID_DIM_NAME)
    else:
        write_jules_top_2d(topmodel_fn, topmodel_maps, X_DIM_NAME, Y_DIM_NAME)

def write_jules_rivers_props(routing_fn):
    accum_ds = rasterio.open(os.environ['ACCUM_FN'])
    draindir_ds = rasterio.open(os.environ['DRAINDIR_FN'])
    routing_maps = {}
    routing_maps['accum_cell'] = accum_ds.read(1, masked=False).squeeze()
    routing_maps['draindir_trip'] = draindir_ds.read(1, masked=False).squeeze()    
    for var in routing_maps.keys():
        arr = routing_maps[var]
        arr = np.ma.masked_array(
            arr,
            mask=np.broadcast_to(
                np.logical_not(LAND_FRAC),
                arr.shape
            ),
            dtype=np.int32,
            fill_value=I4_FILLVAL
        )
        routing_maps[var] = arr
    if ONE_D:
        write_jules_rivers_props_1d(routing_fn, routing_maps, GRID_DIM_NAME)
    else:
        write_jules_rivers_props_2d(routing_fn, routing_maps, X_DIM_NAME, Y_DIM_NAME)

@click.command()
@click.option(
    '-d', 'destdir', nargs=1, default='.', type=str,
    help='Destination directory.'
)
def main(destdir):

    file_suffix = PRODUCT + '_' + REGION + '.nc'    
    if LAND_FRAC:
        land_frac_fn = os.path.join(
            destdir, 'jules_land_frac_' + file_suffix
        )
        if ONE_D:
            write_jules_land_frac_1d(land_frac_fn, GRID_DIM_NAME)
        else:
            write_jules_land_frac_2d(land_frac_fn, X_DIM_NAME, Y_DIM_NAME)

    if LATLON:
        latlon_fn = os.path.join(
            destdir, 'jules_latlon_' + file_suffix
        )
        if ONE_D:
            write_jules_latlon_1d(latlon_fn, GRID_DIM_NAME)
        else:
            write_jules_latlon_2d(latlon_fn, X_DIM_NAME, Y_DIM_NAME)

    # years = [2015]
    years = [yr for yr in range(1992,2015+1)]
    for year in years:
        if FIVEPFT:
            if ANTSFORMAT:
                frac_fn = os.path.join(
                    destdir, 'jules_frac_5pft_ants_' + str(year) + '_' + file_suffix
                )
                write_jules_frac_ants(year, LC_NAMES_5PFT, frac_fn)
                
            frac_fn = os.path.join(
                destdir, 'jules_frac_5pft_' + str(year) + '_' + file_suffix
            )
            surf_hgt_fn = os.path.join(
                destdir, 'jules_surf_hgt_5pft_' + str(year) + '_' + file_suffix
            )
            write_jules_frac(year, LC_NAMES_5PFT, frac_fn, surf_hgt_fn)
                
        if NINEPFT:            
            if ANTSFORMAT:
                frac_fn = os.path.join(
                    destdir, 'jules_frac_9pft_ants_' + str(year) + '_' + file_suffix
                )
                write_jules_frac_ants(year, LC_NAMES_9PFT, frac_fn)
                
            frac_fn = os.path.join(
                destdir, 'jules_frac_9pft_' + str(year) + '_' + file_suffix
            )
            surf_hgt_fn = os.path.join(
                destdir, 'jules_surf_hgt_9pft_' + str(year) + '_' + file_suffix
            )
            write_jules_frac(year, LC_NAMES_9PFT, frac_fn, surf_hgt_fn)

        # To write soil data we need to get the ice fraction, which
        # we retrieve directly from the land cover fraction data.
        # This means that soil data can only be written if land
        # cover data is also written.
        nco = netCDF4.Dataset(frac_fn, 'r', format='NETCDF4')
        ice_frac = nco.variables['frac'][-1, ...].astype(np.bool)
        nco.close()
        if COSBY:
            soil_fn = os.path.join(
                destdir, 'jules_soil_props_' + str(year) + '_cosby_' + file_suffix
            )
            write_jules_soil_props(year, 'cosby', ice_frac, soil_fn)

        if TOMAS:
            soil_fn = os.path.join(
                destdir, 'jules_soil_props_' + str(year) + '_tomas_' + file_suffix
            )
            write_jules_soil_props(year, 'tomas', ice_frac, soil_fn)

        if ROSETTA:
            soil_fn = os.path.join(
                destdir, 'jules_soil_props_' + str(year) + '_rosetta3_' + file_suffix
            )
            write_jules_soil_props(year, 'rosetta3', ice_frac, soil_fn)
            
    if OVERBANK:
        overbank_fn = os.path.join(
            destdir, 'jules_overbank_props_' + file_suffix
        )
        write_jules_overbank_props(overbank_fn)

    if PDM:
        pdm_fn = os.path.join(
            destdir, 'jules_pdm_' + file_suffix
        )
        write_jules_pdm(pdm_fn)

    if TOPMODEL:
        topmodel_fn = os.path.join(
            destdir, 'jules_top_' + file_suffix
        )
        write_jules_top(topmodel_fn)

    if ROUTING:
        routing_fn = os.path.join(
            destdir, 'jules_rivers_props_' + file_suffix
        )
        write_jules_rivers_props(routing_fn)


if __name__ == '__main__':
    main()
