#!/usr/bin/env python3

import os
import numpy as np
import netCDF4
import logging

from subprocess import PIPE

import grass.script as gscript

from grass.script import array as garray 
from grass.script import core as grass 

from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r

from jamr.process.ancillarydataset import AncillaryDataset
from jamr.utils.grass_utils import *
from jamr.utils.utils import (raster2array, add_lat_lon_dims_2d, F8_FILLVAL, F4_FILLVAL, I4_FILLVAL)

LOGGER = logging.getLogger(__name__)


class LandCoverFractionFactory:
    @staticmethod
    def create_landcover_fraction(method, npft, config, inputdata, overwrite):
        if method == 'Poulter':
            if npft == 5:
                return Poulter2015FivePFT(config, inputdata, overwrite)
            elif npft == 9: 
                return Poulter2015NinePFT(config, inputdata, overwrite)


# In original, urban was allocated as follows: 
# trees_broadleaf_deciduous (0.025)
# trees_needleleaf_evergreen (0.025)
# natural_grass (0.15)
# bare_soil (0.75)
# water (0.05)
# Here, we allocate urban to an urban non-vegetated PFT
ADJUSTED_POULTER_CROSSWALK = {
    'trees_broadleaf_evergreen': {
        30: 0.05, 40: 0.05, 50: 0.90, 100: 0.1, 110: 0.05, 150: 0.01, 160: 0.3, 170: 0.6
    },
    'trees_broadleaf_deciduous': {
        30: 0.05, 40: 0.05, 60: 0.70, 61: 0.70, 62: 0.30, 90: 0.30, 100: 0.20, 
        110: 0.10, 150: 0.03, 151: 0.02, 160: 0.30, 180: 0.05 #, 190: 0.025
    },
    'trees_needleleaf_evergreen': {
        70: 0.70, 71: 0.70, 72: 0.30, 90: 0.20, 100: 0.05, 110: 0.05, 150: 0.01, 151: 0.06, 180: 0.10 #, 190: 0.025
    },
    'trees_needleleaf_deciduous': {
        80: 0.70, 81: 0.70, 82: 0.30, 90: 0.10, 100: 0.05, 151: 0.02
    },
    'shrubs_broadleaf_evergreen': {
        30: 0.05, 40: 0.075, 50: 0.05, 70: 0.05, 71: 0.05, 80: 0.05, 81: 0.05, 
        90: 0.05, 100: 0.05, 110: 0.05, 120: 0.20, 121: 0.30, 150: 0.01, 152: 0.02, 170: 0.20
    },
    "shrubs_broadleaf_deciduous": {
        12: 0.50, 30: 0.05, 40: 0.10, 50: 0.05, 60: 0.15, 61: 0.15, 62: 0.25, 
        70: 0.05, 71: 0.05, 72: 0.05, 80: 0.05, 81: 0.05, 82: 0.05, 90: 0.05, 100: 0.10, 110: 0.10, 120: 0.20, 122: 0.60, 150: 0.03, 152: 0.06, 180: 0.10
    },
    "shrubs_needleleaf_evergreen": {
        30: 0.05, 40: 0.075, 70: 0.05, 71: 0.05, 72: 0.05, 80: 0.05, 81: 0.05, 
        82: 0.05, 90: 0.05, 100: 0.05, 110: 0.05, 120: 0.20, 121: 0.30, 150: 0.01, 152: 0.02, 180: 0.05
    }, 
    "shrubs_needleleaf_deciduous": {},
    "natural_grass": {
        30: 0.15, 40: 0.25, 60: 0.15, 61: 0.15, 62: 0.35, 70: 0.15, 71: 0.15, 
        72: 0.30, 80: 0.15, 81: 0.15, 82: 0.30, 90: 0.15, 100: 0.40, 110: 0.60, 
        120: 0.20, 121: 0.20, 122: 0.20, 130: 0.60, 140: 0.60, 150: 0.05, 
        151: 0.05, 152: 0.05, 153: 0.15, 160: 0.20, 180: 0.40 #, 190: 0.15
    },
    "crops": {
        10: 1.0, 11: 1.0, 12: 0.50, 20: 1.0, 30: 0.6, 40: 0.4
    }, 
    "bare_soil": {
        62: 0.10, 72: 0.30, 82: 0.30, 90: 0.10, 120: 0.20, 121: 0.20, 122: 0.20, 
        130: 0.40, 140: 0.40, 150: 0.85, 151: 0.85, 152: 0.85, 153: 0.85, 
        # 190: 0.75, 
        200: 1.0, 201: 1.0, 202: 1.0},
    "water": {
        160: 0.20, 170: 0.20, 180: 0.30, 
        # 190: 0.05, 
        210: 1.0}, 
    "urban": {190: 1},
    "snow_ice": {220: 1}
}


# CHECK SUM TO 1.
# all_keys = []
# for k,v in ADJUSTED_POULTER_CROSSWALK.items():
#     for kk,vv in v.items():
#         all_keys.append(kk)
# all_keys = list(set(all_keys))
# vals = {}
# for key in all_keys:
#     vals[key] = 0.
#     for k,v in ADJUSTED_POULTER_CROSSWALK.items():
#         if key in v.keys():
#             vals[key] += v[key]


class _Poulter2015PFT:
    def __init__(self, config, landcover, overwrite):
        self.config = config
        self.landcover = landcover 
        self.years = self.landcover.years
        self.pft_names = list(ADJUSTED_POULTER_CROSSWALK.keys())
        self.crosswalk = ADJUSTED_POULTER_CROSSWALK
        self.overwrite = overwrite 
        self.region_name = config['region']['name']
        self.set_mapnames()

    def initial(self):
        pass

    def _write_reclass_rules(self, pft, factor=1000):
        # TODO can also do this with r.category + r.mapcalc
        try:
            index = self.pft_names.index(pft)
        except:
            ValueError()

        pft_crosswalk = self.crosswalk[pft]
        text = ""
        for key, value in pft_crosswalk.items():
            ln = str(key) + " = " + str(int(value * factor)) + os.linesep
            text = text + ln
        text = text + "* = 0"
        # for key, value in pft_crosswalk.items():
        #     ln = str(key) + ":" + str(value) + os.linesep
        #     text = text + ln
        with open("/tmp/rules.txt", "w") as f:
            f.write(text)

    def set_mapnames(self):
        mapnames = {}
        for year in self.years:
            year_mapnames = {} 
            for pft in self.pft_names:
                year_mapnames[pft] = f'esacci_lc_{pft}_{year}_{self.region_name}'
            
            mapnames[year] = year_mapnames

        self.mapnames = mapnames 

    def _create_pft_map(self, year, pft):
        input_map = self.landcover.mapnames[year]
        output_map = self.mapnames[year][pft]

        # r.reclass only works with integers, so we multiply by a suitably 
        # large factor to convert the fractions in the crosswalk table to integers 
        # the alternative would be to use a python dictionary with pft fractions
        mult_factor = 1000
        self._write_reclass_rules(pft, factor=mult_factor)
        
        # g.region(raster=input_map)
        p = gscript.start_command('r.reclass', 
                                  input=input_map, 
                                  output=output_map + '_step1', 
                                  rules='/tmp/rules.txt', 
                                  overwrite=self.overwrite, stderr=PIPE)
        stdout, stderr = p.communicate()

        # Divide by factor used to convert percentages to integers in step 1 
        p = gscript.start_command('r.mapcalc', 
                                  expression=f'{output_map} = {output_map}_step1 / {mult_factor}.0', 
                                  overwrite=self.overwrite, 
                                  stderr=PIPE)
        stdout, stderr = p.communicate()

        # # Intermediate output 
        # r.out_gdal(input=output_map, 
        #            output=os.path.join(self.config['main']['output_directory'], output_map + ".tif"),
        #            createopt="COMPRESS=DEFLATE",
        #            overwrite=True)

        # self._write_reclass_rules(pft)
        # g.region(raster=input_map)
        # p = gscript.start_command('r.category',
        #                           map=input_map,
        #                           separator=":",
        #                           rules='/tmp/rules.txt',
        #                           stderr=PIPE)
        # stdout, stderr = p.communicate()
        # p = gscript.start_command('r.mapcalc',
        #                           expression=f'{output_map} = @{input_map}',
        #                           overwrite=self.overwrite,
        #                           stderr=PIPE)
        # stdout, stderr = p.communicate()

    def compute(self):
        # This converts the discrete classes of the ESA land cover map to the 
        # fractions outlined in Poulter et al. (2015)
        for year in self.years:
            for pft in self.pft_names:
                LOGGER.info(f'Creating {pft} map from land cover map')
                self._create_pft_map(year, pft)


JULES_5PFT_NAMES = [
    'tree_broadleaf', 'tree_needleleaf', 'shrub', 'c3_grass', 'c4_grass', 
    'urban', 'water', 'bare_soil', 'snow_ice'
]
JULES_9PFT_NAMES = [
    'tree_broadleaf_evergreen_tropical', 'tree_broadleaf_evergreen_temperate', 
    'tree_broadleaf_deciduous', 'tree_needleleaf_evergreen', 'tree_needleleaf_deciduous', 
    'shrub_evergreen', 'shrub_deciduous', 'c3_grass', 'c4_grass', 
    'urban', 'water', 'bare_soil', 'snow_ice'
]


class Poulter2015JulesPFT(AncillaryDataset):
    def __init__(self, config, inputdata, npft, overwrite):
        # TODO supply landmask
        self.config = config 
        self.inputdata = inputdata 
        self.years = inputdata.landcover.years 
        if npft == 5:
            pft_names = JULES_5PFT_NAMES 
        elif npft == 9:
            pft_names = JULES_9PFT_NAMES
        self.pft_names = pft_names
        self.overwrite = overwrite 
        self.region_name = config['region']['name']
        self._set_mapnames()

    def _compute_pfts(self):
        # self._set_native_region()
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        self.pfts = _Poulter2015PFT(self.config, self.inputdata.landcover, self.overwrite)
        self.pfts.initial()
        self.pfts.compute()

    def _set_mapnames(self):
        mapnames_native = {}
        mapnames = {}
        weighted_elev_mapnames_native = {}
        weighted_elev_mapnames = {}
        weights_mapnames = {}
        surf_hgt_mapnames = {}
        for year in self.years:
            year_mapnames_native = {}
            year_mapnames = {} 
            year_weighted_elev_mapnames_native = {}
            year_weighted_elev_mapnames = {}
            year_weights_mapnames = {}
            year_surf_hgt_mapnames = {}
            for pft in self.pft_names:
                year_mapnames_native[pft] = f'{pft}_{year}_{self.region_name}_native'
                year_mapnames[pft] = f'{pft}_{year}_{self.region_name}'
                year_weighted_elev_mapnames_native[pft] = f'{pft}_{year}_weighted_elev_{self.region_name}_native'
                year_weighted_elev_mapnames[pft] = f'{pft}_{year}_weighted_elev_{self.region_name}'
                year_weights_mapnames[pft] = f'{pft}_{year}_weights_{self.region_name}'
                year_surf_hgt_mapnames[pft] = f'{pft}_{year}_surf_hgt_{self.region_name}'
            
            mapnames_native[year] = year_mapnames_native 
            mapnames[year] = year_mapnames
            weighted_elev_mapnames_native[year] = year_weighted_elev_mapnames_native
            weighted_elev_mapnames[year] = year_weighted_elev_mapnames 
            weights_mapnames[year] = year_weights_mapnames
            surf_hgt_mapnames[year] = year_surf_hgt_mapnames
        
        self.mapnames_native = mapnames_native
        self.mapnames = mapnames 
        self.weighted_elev_mapnames_native = weighted_elev_mapnames_native
        self.weighted_elev_mapnames = weighted_elev_mapnames
        self.weights_mapnames = weights_mapnames
        self.surf_hgt_mapnames = surf_hgt_mapnames

        # Get elevation resampled to native land cover map resolution
        self.elevation_mapname_native = self.inputdata.elevation.mapnames['globe_0.002778Deg']
        self.elevation_mapname = f'elev_{self.region_name}'

    def compute(self):
        raise NotImplementedError 

    def compute_surf_hgt(self, year):

        # Resample elevation map to the native landcover resolution 
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        # Note `native` here refers to the native resolution of the elevation map
        self._resample(input_map=self.elevation_mapname_native, output_map=self.elevation_mapname, method='average')

        for pft in self.pft_names:
            LOGGER.info(f'Computing surface height map for {pft}')
            native_weighted_elev_map = self.weighted_elev_mapnames_native[year][pft]
            native_lc_map = self.mapnames_native[year][pft]
            native_elev_map = self.elevation_mapname
            weighted_elev_map = self.weighted_elev_mapnames[year][pft]
            weights_map = self.weights_mapnames[year][pft] 
            surf_hgt_map = self.surf_hgt_mapnames[year][pft]
            self._set_native_region(self.inputdata.landcover.mapnames[2015])
            p = gscript.start_command('r.mapcalc',
                                      expression=f'{native_weighted_elev_map} = {native_lc_map} * {native_elev_map}',
                                      overwrite=self.overwrite,
                                      stderr=PIPE)
            stdout, stderr = p.communicate()
            self._set_target_region()
            self._resample(input_map=native_weighted_elev_map, output_map=weighted_elev_map, method='sum')
            self._resample(input_map=native_lc_map, output_map=weights_map, method='sum')
            p = gscript.start_command('r.mapcalc',
                                      expression=f'{surf_hgt_map} = {weighted_elev_map} / {weights_map}',
                                      overwrite=self.overwrite,
                                      stderr=PIPE)
            stdout, stderr = p.communicate()

    def compute_c3_grass(self, year):
        LOGGER.info(f'Computing C3 grass')
        native_output_map = self.mapnames_native[year]['c3_grass']
        output_map = self.mapnames[year]['c3_grass']
        natural_grass_map = self.pfts.mapnames[year]['natural_grass']
        managed_grass_map = self.pfts.mapnames[year]['crops']
        c4_natural_vegetation_fraction_map = self.inputdata.c4fraction.mapnames[2015]['C4_grass_area']
        c4_crop_fraction_map = self.inputdata.c4fraction.mapnames[2015]['C4_crop_area']
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc',
                                  expression=f'{native_output_map} = ({natural_grass_map} * (1. - {c4_natural_vegetation_fraction_map} / 100.)) + ({managed_grass_map} * (1. - {c4_crop_fraction_map} / 100.))',
                                  overwrite=self.overwrite,
                                  stderr=PIPE)
        p.communicate()
        # r.out_gdal(input=c4_natural_vegetation_fraction_map, 
        #            output=os.path.join(self.config['main']['output_directory'], c4_natural_vegetation_fraction_map + ".tif"),
        #            createopt="COMPRESS=DEFLATE",
        #            overwrite=True)
        # r.out_gdal(input=c4_crop_fraction_map, 
        #            output=os.path.join(self.config['main']['output_directory'], c4_crop_fraction_map + ".tif"),
        #            createopt="COMPRESS=DEFLATE",
        #            overwrite=True)
        # r.out_gdal(input=natural_grass_map, 
        #            output=os.path.join(self.config['main']['output_directory'], natural_grass_map + ".tif"),
        #            createopt="COMPRESS=DEFLATE",
        #            overwrite=True)
        # r.out_gdal(input=managed_grass_map, 
        #            output=os.path.join(self.config['main']['output_directory'], managed_grass_map + ".tif"),
        #            createopt="COMPRESS=DEFLATE",
        #            overwrite=True)
        # r.out_gdal(input=self.inputdata.landcover.mapnames[2015], output=os.path.join(self.config['main']['output_directory'], 'land_cover_2015.tif'), createopt="COMPRESS=DEFLATE", overwrite=True)
        # r.out_gdal(input=native_output_map, 
        #            output=os.path.join(self.config['main']['output_directory'], native_output_map + ".tif"),
        #            createopt="COMPRESS=DEFLATE",
        #            overwrite=True)
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')
        # r.out_gdal(input=output_map, 
        #            output=os.path.join(self.config['main']['output_directory'], output_map + ".tif"),
        #            createopt="COMPRESS=DEFLATE",
        #            overwrite=True)

    def compute_c4_grass(self, year):
        LOGGER.info(f'Computing C4 grass')
        native_output_map = self.mapnames_native[year]['c4_grass']
        output_map = self.mapnames[year]['c4_grass']
        natural_grass_map = self.pfts.mapnames[year]['natural_grass']
        managed_grass_map = self.pfts.mapnames[year]['crops']
        c4_natural_vegetation_fraction_map = self.inputdata.c4fraction.mapnames[2015]['C4_grass_area']
        c4_crop_fraction_map = self.inputdata.c4fraction.mapnames[2015]['C4_crop_area']
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc',
                                  expression=f'{native_output_map} = ({natural_grass_map} * {c4_natural_vegetation_fraction_map} / 100.) + ({managed_grass_map} * {c4_crop_fraction_map} / 100.)',
                                  overwrite=self.overwrite,
                                  stderr=PIPE)
        p.communicate()
        # r.out_gdal(input=native_output_map, 
        #            output=os.path.join(self.config['main']['output_directory'], native_output_map + ".tif"),
        #            createopt="COMPRESS=DEFLATE",
        #            overwrite=True)
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')
        # r.out_gdal(input=output_map, 
        #            output=os.path.join(self.config['main']['output_directory'], output_map + ".tif"),
        #            createopt="COMPRESS=DEFLATE",
        #            overwrite=True)

    def compute_urban(self, year):
        LOGGER.info(f'Computing urban land')
        native_output_map = self.mapnames_native[year]['urban']
        output_map = self.mapnames[year]['urban']
        urban_map = self.pfts.mapnames[year]['urban']
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc',
                                  expression=f'{native_output_map} = {urban_map}',
                                  overwrite=self.overwrite,
                                  stderr=PIPE)
        p.communicate()
        # r.out_gdal(input=native_output_map, 
        #            output=os.path.join(self.config['main']['output_directory'], native_output_map + ".tif"),
        #            createopt="COMPRESS=DEFLATE",
        #            overwrite=True)
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')

    def compute_water(self, year):
        LOGGER.info(f'Computing water')
        native_output_map = self.mapnames_native[year]['water']
        output_map = self.mapnames[year]['water']
        water_map = self.pfts.mapnames[year]['water']
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc',
                                  expression=f'{native_output_map} = {water_map}',
                                  overwrite=self.overwrite,
                                  stderr=PIPE)
        p.communicate()
        # r.out_gdal(input=native_output_map, 
        #            output=os.path.join(self.config['main']['output_directory'], native_output_map + ".tif"),
        #            createopt="COMPRESS=DEFLATE",
        #            overwrite=True)
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')

    def compute_bare_soil(self, year):
        LOGGER.info(f'Computing bare soil')
        native_output_map = self.mapnames_native[year]['bare_soil']
        output_map = self.mapnames[year]['bare_soil']
        bare_soil_map = self.pfts.mapnames[year]['bare_soil']
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc',
                                  expression=f'{native_output_map} = {bare_soil_map}', 
                                  overwrite=self.overwrite,
                                  stderr=PIPE)
        p.communicate()
        # r.out_gdal(input=native_output_map, 
        #            output=os.path.join(self.config['main']['output_directory'], native_output_map + ".tif"),
        #            createopt="COMPRESS=DEFLATE",
        #            overwrite=True)
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')

    def compute_snow_ice(self, year):
        LOGGER.info(f'Computing snow/ice')
        native_output_map = self.mapnames_native[year]['snow_ice']
        output_map = self.mapnames[year]['snow_ice']
        snow_ice_map = self.pfts.mapnames[year]['snow_ice']
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc',
                                  expression=f'{native_output_map} = {snow_ice_map}', 
                                  overwrite=self.overwrite,
                                  stderr=PIPE)
        p.communicate()
        # r.out_gdal(input=native_output_map, 
        #            output=os.path.join(self.config['main']['output_directory'], native_output_map + ".tif"),
        #            createopt="COMPRESS=DEFLATE",
        #            overwrite=True)
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')

    def get_data_arrays(self, year):
        frac_list = []
        surf_hgt_list = []
        for pft in self.pft_names:
            frac = garray.array(mapname=self.mapnames[year][pft])
            surf_hgt = garray.array(mapname=self.surf_hgt_mapnames[year][pft])
            frac_list.append(frac)
            surf_hgt_list.append(surf_hgt)

        frac = np.stack(frac_list)
        frac /= frac.sum(axis=0)
        surf_hgt = np.stack(surf_hgt_list)

        # # Compute weighted mean of all cells (for ice cells)
        # mean_surf_hgt = (
        #     np.sum(surf_hgt * frac, axis=0)
        #     / np.sum(frac, axis=0)
        # )
        
        # # Compute weighted mean of soil and ice cells (for non-ice cells)
        # soil_ice_sum = np.sum(frac[-2:, ...], axis=0)
        # mean_surf_hgt_soil_ice = np.divide(
        #     np.sum(surf_hgt[-2:, ...] * frac[-2:, ...], axis=0),
        #     soil_ice_sum,
        #     out=np.zeros_like(soil_ice_sum),
        #     where=soil_ice_sum>0
        # )
        # mean_surf_hgt_soil_ice = (
        #     np.sum(surf_hgt[-2:, ...] * frac[-2:, ...], axis=0)
        #     / np.sum(frac[-2:, ...], axis=0)
        # )

        # # original ice/soil fractions
        # ice_orig = frac[-1, ...]
        # soil_orig = frac[-2, ...]

        # ice = np.zeros_like(ice_orig).astype(bool)
        # ice[ice_orig > 0.5] = True
        # not_ice = np.logical_not(ice)

        # # initially set all fractions/heights in ice gridboxes to zero
        # frac *= not_ice[None, ...]
        # surf_hgt *= not_ice[None, ...]
        # # then set ice fraction to one
        # frac[-1][ice] = 1
        # frac[-1][not_ice] = 0
        # # in non-ice gridboxes, add original ice fraction to bare soil
        # frac[-2] = (soil_orig + ice_orig) * not_ice
        # # surface height in ice grid boxes is the mean of all fractions
        # surf_hgt[-1][ice] = mean_surf_hgt[ice]
        # # surface height in non-ice is the weighted mean of bare soil
        # # and original ice fraction
        # surf_hgt[-2][not_ice] = mean_surf_hgt_soil_ice[not_ice]
        # # divide by sum again, to ensure fractions continue to sum to one
        # frac /= frac.sum(axis=0)
        return frac, surf_hgt

    def write_netcdf(self, landfrac_mapname):
        coords, bnds, land_frac = raster2array(landfrac_mapname)

        x_dim_name = 'x'
        y_dim_name = 'y'
        type_dim_name = 'type'

        for year in self.years:
            # Collect data for all PFTs
            frac, surf_hgt = self.get_data_arrays(year)
            mask = np.broadcast_to(np.logical_not(land_frac), frac.shape)
            frac = np.ma.array(frac, mask=mask, dtype=np.float64, fill_value=F8_FILLVAL)
            surf_hgt = np.ma.array(surf_hgt, mask=mask, dtype=np.float64, fill_value=F8_FILLVAL)
            output_filename = os.path.join(self.config['main']['output_directory'], f'jamr_frac_{year}.nc')
            write_jules_frac_2d(frac, surf_hgt, output_filename, coords[0], coords[1], bnds[0], bnds[1], x_dim_name, y_dim_name, type_dim_name)


def write_jules_frac_2d(frac_input, surf_hgt_input, output_filename, x_vals, y_vals, x_bnds, y_bnds, x_dim_name, y_dim_name, type_dim_name):
    nco = netCDF4.Dataset(output_filename, 'w', format='NETCDF4')
    ntype = frac_input.shape[0]
    nco = add_lat_lon_dims_2d(nco, x_dim_name, y_dim_name, x_vals, y_vals, x_bnds, y_bnds)

    nco.createDimension(type_dim_name, ntype)
    var = nco.createVariable(type_dim_name, 'i4', (type_dim_name,))
    var.units = '1'
    var.standard_name = type_dim_name
    var.long_name = type_dim_name
    var[:] = np.arange(1, ntype+1)
    
    var = nco.createVariable(
        'frac', 'f8', (type_dim_name, y_dim_name, x_dim_name),
        fill_value=F8_FILLVAL
    )
    var.units = '1'
    var.standard_name = 'frac'
    var.grid_mapping = 'latitude_longitude'
    var[:] = frac_input

    var = nco.createVariable(
        'surf_hgt', 'f8', (type_dim_name, y_dim_name, x_dim_name),
        fill_value=F8_FILLVAL
    )
    var.units = '1'
    var.standard_name = 'surf_hgt'
    var.grid_mapping = 'latitude_longitude'
    var[:] = surf_hgt_input

    nco.close()


class Poulter2015FivePFT(Poulter2015JulesPFT):
    def __init__(self, config, inputdata, overwrite):
        super().__init__(config, inputdata, 5, overwrite)

    def compute(self, landfrac_mapname):
        
        # Apply mask based on supplied land fraction map 
        r.mask(raster=landfrac_mapname, maskcats=1)

        # Set PFT fractions from Poulter et al.
        self._compute_pfts()

        # Compute JULES PFTs
        self.compute_tree_broadleaf(2015)
        self.compute_tree_needleleaf(2015) 
        self.compute_shrub(2015)
        self.compute_c3_grass(2015)
        self.compute_c4_grass(2015)
        self.compute_urban(2015)
        self.compute_water(2015)
        self.compute_bare_soil(2015)
        self.compute_snow_ice(2015)

        # Compute surface heights for each JULES PFT
        self.compute_surf_hgt(2015)

        # Remove mask 
        r.mask(flags='r')

    def compute_tree_broadleaf(self, year):
        LOGGER.info(f'Computing broadleaf tree')
        native_output_map = self.mapnames_native[year]['tree_broadleaf']
        output_map = self.mapnames[year]['tree_broadleaf']
        tree_broadleaf_deciduous_map = self.pfts.mapnames[year]['trees_broadleaf_deciduous']
        tree_broadleaf_evergreen_map = self.pfts.mapnames[year]['trees_broadleaf_evergreen']
        print(tree_broadleaf_deciduous_map)
        print(tree_broadleaf_evergreen_map)
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc', 
                                  expression=f'{native_output_map} = {tree_broadleaf_deciduous_map} + {tree_broadleaf_evergreen_map}',
                                  overwrite=self.overwrite, 
                                  stderr=PIPE)
        p.communicate()
        # r.out_gdal(input=native_output_map, 
        #            output=os.path.join(self.config['main']['output_directory'], native_output_map + ".tif"),
        #            createopt="COMPRESS=DEFLATE",
        #            overwrite=True)
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')

    def compute_tree_needleleaf(self, year):
        LOGGER.info(f'Computing needleleaf tree')
        native_output_map = self.mapnames_native[year]['tree_needleleaf']
        output_map = self.mapnames[year]['tree_needleleaf']
        tree_needleleaf_deciduous_map = self.pfts.mapnames[year]['trees_needleleaf_deciduous']
        tree_needleleaf_evergreen_map = self.pfts.mapnames[year]['trees_needleleaf_evergreen']
        print(tree_needleleaf_deciduous_map)
        print(tree_needleleaf_evergreen_map)
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc', 
                                  expression=f'{native_output_map} = {tree_needleleaf_deciduous_map} + {tree_needleleaf_evergreen_map}', 
                                  overwrite=self.overwrite, 
                                  stderr=PIPE)
        p.communicate()
        # r.out_gdal(input=native_output_map, 
        #            output=os.path.join(self.config['main']['output_directory'], native_output_map + ".tif"),
        #            createopt="COMPRESS=DEFLATE",
        #            overwrite=True)
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')

    def compute_shrub(self, year):
        LOGGER.info(f'Computing shrub')
        native_output_map = self.mapnames_native[year]['shrub']
        output_map = self.mapnames[year]['shrub']
        shrub_broadleaf_deciduous_map = self.pfts.mapnames[year]['shrubs_broadleaf_deciduous'] 
        shrub_broadleaf_evergreen_map = self.pfts.mapnames[year]['shrubs_broadleaf_evergreen'] 
        shrub_needleleaf_deciduous_map = self.pfts.mapnames[year]['shrubs_needleleaf_deciduous'] 
        shrub_needleleaf_evergreen_map = self.pfts.mapnames[year]['shrubs_needleleaf_evergreen']
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc', 
                                  expression=f'{native_output_map} = {shrub_broadleaf_deciduous_map} + {shrub_broadleaf_evergreen_map} + {shrub_needleleaf_deciduous_map} + {shrub_needleleaf_evergreen_map}',
                                  overwrite=self.overwrite,
                                  stderr=PIPE)
        p.communicate()
        # r.out_gdal(input=native_output_map, 
        #            output=os.path.join(self.config['main']['output_directory'], native_output_map + ".tif"),
        #            createopt="COMPRESS=DEFLATE",
        #            overwrite=True)
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')


class Poulter2015NinePFT(Poulter2015JulesPFT):
    def __init__(self, config, inputdata, overwrite):
        super().__init__(config, inputdata, 9, overwrite)
    
    def compute(self, landfrac_mapname):
        
        # Apply mask based on supplied land fraction map 
        r.mask(raster=landfrac_mapname, maskcats=1)

        # Set PFT fractions from Poulter et al.
        self._compute_pfts()

        # Compute JULES PFTs
        self.compute_tree_broadleaf_evergreen_tropical(2015)
        self.compute_tree_broadleaf_evergreen_temperate(2015)
        self.compute_tree_broadleaf_deciduous(2015) 
        self.compute_tree_needleleaf_deciduous(2015) 
        self.compute_tree_needleleaf_evergreen(2015)
        self.compute_shrub_evergreen(2015)
        self.compute_shrub_deciduous(2015)
        self.compute_c3_grass(2015)
        self.compute_c4_grass(2015)
        self.compute_urban(2015)
        self.compute_water(2015)
        self.compute_bare_soil(2015)
        self.compute_snow_ice(2015)

        # Compute surface elevation
        self.compute_surf_hgt(2015)

        # Remove mask
        r.mask(flags='r')

    def compute_tree_broadleaf_evergreen_tropical(self, year):
        native_output_map = self.mapnames_native[year]['tree_broadleaf_evergreen_tropical']
        output_map = self.mapnames[year]['tree_broadleaf_evergreen_tropical']
        tree_broadleaf_evergreen_map = self.pfts.mapnames[year]['trees_broadleaf_evergreen']
        tropical_broadleaf_forest_map = self.inputdata.ecoregions.mapnames[0]
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc', 
                                  expression=f'{native_output_map} = {tree_broadleaf_evergreen_map} * {tropical_broadleaf_forest_map}',
                                  overwrite=self.overwrite, 
                                  stderr=PIPE)
        p.communicate()
        # r.out_gdal(input=native_output_map, 
        #            output=os.path.join(self.config['main']['output_directory'], native_output_map + ".tif"),
        #            createopt="COMPRESS=DEFLATE",
        #            overwrite=True)
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')

    def compute_tree_broadleaf_evergreen_temperate(self, year):
        native_output_map = self.mapnames_native[year]['tree_broadleaf_evergreen_temperate']
        output_map = self.mapnames[year]['tree_broadleaf_evergreen_temperate']
        tree_broadleaf_evergreen_map = self.pfts.mapnames[year]['trees_broadleaf_evergreen']
        tropical_broadleaf_forest_map = self.inputdata.ecoregions.mapnames[0]
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc', 
                                  expression=f'{native_output_map} = {tree_broadleaf_evergreen_map} * (1-{tropical_broadleaf_forest_map})',
                                  overwrite=self.overwrite, 
                                  stderr=PIPE)
        p.communicate()
        # r.out_gdal(input=native_output_map, 
        #            output=os.path.join(self.config['main']['output_directory'], native_output_map + ".tif"),
        #            createopt="COMPRESS=DEFLATE",
        #            overwrite=True)
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')

    def compute_tree_broadleaf_deciduous(self, year):
        native_output_map = self.mapnames_native[year]['tree_broadleaf_deciduous']
        output_map = self.mapnames[year]['tree_broadleaf_deciduous']
        tree_broadleaf_deciduous_map = self.pfts.mapnames[year]['trees_broadleaf_deciduous']
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc', 
                                  expression=f'{native_output_map} = {tree_broadleaf_deciduous_map}',
                                  overwrite=self.overwrite, 
                                  stderr=PIPE)
        p.communicate()
        # r.out_gdal(input=native_output_map, 
        #            output=os.path.join(self.config['main']['output_directory'], native_output_map + ".tif"),
        #            createopt="COMPRESS=DEFLATE",
        #            overwrite=True)
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')

    def compute_tree_needleleaf_evergreen(self, year):
        native_output_map = self.mapnames_native[year]['tree_needleleaf_evergreen']
        output_map = self.mapnames[year]['tree_needleleaf_evergreen']
        tree_needleleaf_evergreen_map = self.pfts.mapnames[year]['trees_needleleaf_evergreen']
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc', 
                                  expression=f'{native_output_map} = {tree_needleleaf_evergreen_map}',
                                  overwrite=self.overwrite, 
                                  stderr=PIPE)
        p.communicate()
        # r.out_gdal(input=native_output_map, 
        #            output=os.path.join(self.config['main']['output_directory'], native_output_map + ".tif"),
        #            createopt="COMPRESS=DEFLATE",
        #            overwrite=True)
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')

    def compute_tree_needleleaf_deciduous(self, year):
        native_output_map = self.mapnames_native[year]['tree_needleleaf_deciduous']
        output_map = self.mapnames[year]['tree_needleleaf_deciduous']
        tree_needleleaf_deciduous_map = self.pfts.mapnames[year]['trees_needleleaf_deciduous']
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc', 
                                  expression=f'{native_output_map} = {tree_needleleaf_deciduous_map}',
                                  overwrite=self.overwrite, 
                                  stderr=PIPE)
        p.communicate()
        # r.out_gdal(input=native_output_map, 
        #            output=os.path.join(self.config['main']['output_directory'], native_output_map + ".tif"),
        #            createopt="COMPRESS=DEFLATE",
        #            overwrite=True)
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')
    
    def compute_shrub_evergreen(self, year):
        native_output_map = self.mapnames_native[year]['shrub_evergreen']
        output_map = self.mapnames[year]['shrub_evergreen']
        shrub_broadleaf_evergreen_map = self.pfts.mapnames[year]['shrubs_broadleaf_evergreen'] 
        shrub_needleleaf_evergreen_map = self.pfts.mapnames[year]['shrubs_needleleaf_evergreen']
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc', 
                                  expression=f'{native_output_map} = {shrub_broadleaf_evergreen_map} + {shrub_needleleaf_evergreen_map}',
                                  overwrite=self.overwrite, 
                                  stderr=PIPE)
        p.communicate()
        # r.out_gdal(input=native_output_map, 
        #            output=os.path.join(self.config['main']['output_directory'], native_output_map + ".tif"),
        #            createopt="COMPRESS=DEFLATE",
        #            overwrite=True)
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')

    def compute_shrub_deciduous(self, year):
        native_output_map = self.mapnames_native[year]['shrub_deciduous']
        output_map = self.mapnames[year]['shrub_deciduous']
        shrub_broadleaf_deciduous_map = self.pfts.mapnames[year]['shrubs_broadleaf_deciduous'] 
        shrub_needleleaf_deciduous_map = self.pfts.mapnames[year]['shrubs_needleleaf_deciduous']
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc', 
                                  expression=f'{native_output_map} = {shrub_broadleaf_deciduous_map} + {shrub_needleleaf_deciduous_map}',
                                  overwrite=self.overwrite, 
                                  stderr=PIPE)
        p.communicate()
        # r.out_gdal(input=native_output_map, 
        #            output=os.path.join(self.config['main']['output_directory'], native_output_map + ".tif"),
        #            createopt="COMPRESS=DEFLATE",
        #            overwrite=True)
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')


# def write_jules_frac_ants(year, lc_names, frac_fn):
#     frac, _ = get_jules_frac(year, lc_names)    
#     ntype = frac.shape[0]
#     # extract region characteristics, and move western
#     # hemisphere east of east hemisphere.
#     land_frac, lat_vals, lon_vals, extent = get_region_data()
#     nlat = len(lat_vals)
#     nlon = len(lon_vals)
#     lat_bnds = get_lat_lon_bnds(lat_vals, (extent.top, extent.bottom))
#     lon_bnds = get_lat_lon_bnds(lon_vals, (extent.left, extent.right))
#     west_hemisphere = lon_vals < 0.
#     east_hemisphere = ~west_hemisphere
#     frac = np.concatenate([frac[:, :, east_hemisphere], frac[:, :, west_hemisphere]], axis=2)
#     lon_vals = np.concatenate([lon_vals[east_hemisphere], lon_vals[west_hemisphere] + 360.], axis=0)
#     lon_bnds = np.concatenate([lon_bnds[east_hemisphere, :], lon_bnds[west_hemisphere, :] + 360.], axis=0)
#     # create file
#     nco = netCDF4.Dataset(frac_fn, 'w', format='NETCDF4')
#     nco.grid_staggering = 6
    
#     # add dimensions
#     nco.createDimension('dim0', ntype)
#     nco.createDimension('latitude', nlat)
#     nco.createDimension('longitude', nlon)
#     nco.createDimension('bnds', 2)
#     # add variables
#     var = nco.createVariable(
#         'longitude', 'f8', ('longitude',)
#     )
#     var.axis = 'X'
#     var.bounds = 'longitude_bnds'
#     var.units = 'degrees_east'
#     var.standard_name = 'longitude'
#     var[:] = lon_vals
#     var = nco.createVariable(
#         'longitude_bnds', 'f8', ('longitude', 'bnds')
#     )
#     var[:] = lon_bnds
#     var = nco.createVariable(
#         'latitude', 'f8', ('latitude',)
#     )
#     var.axis = 'Y'
#     var.bounds = 'latitude_bnds'
#     var.units = 'degrees_north'
#     var.standard_name = 'latitude'
#     var[:] = lat_vals
#     var = nco.createVariable(
#         'latitude_bnds', 'f8', ('latitude', 'bnds')
#     )
#     var[:] = lat_bnds
#     var = nco.createVariable(
#         'latitude_longitude', 'i4'
#     )
#     var.grid_mapping_name = 'latitude_longitude'
#     var.longitude_of_prime_meridian = 0.
#     var.earth_radius = 6371229.    
#     # TODO: change variable name
#     var = nco.createVariable(
#         'land_cover_lccs', 'f8', ('dim0', 'latitude', 'longitude'),
#         fill_value=F8_FILLVAL
#     )
#     var.units = '1'
#     var.um_stash_source = 'm01s00i216'
#     var.standard_name = 'land_cover_lccs'
#     var.grid_mapping = 'latitude_longitude'
#     var.coordinates = 'pseudo_level'
#     var[:] = frac
        
#     var = nco.createVariable('pseudo_level', 'i4', ('dim0',))
#     var.units = '1'
#     var.long_name = 'pseudo_level'
#     var[:] = np.arange(1, ntype+1)
#     nco.close()
    
# def write_jules_frac_1d(frac_fn, frac, var_name, var_units, grid_dim_name, type_dim_name):
#     nco = netCDF4.Dataset(frac_fn, 'w', format='NETCDF4')
#     ntype, nland = frac.shape[0], frac.shape[1]
#     nco.createDimension(grid_dim_name, nland)
#     nco.createDimension(type_dim_name, ntype)

#     var = nco.createVariable(type_dim_name, 'i4', (type_dim_name,))
#     var.units = '1'
#     var.standard_name = type_dim_name
#     var.long_name = type_dim_name
#     var[:] = np.arange(1, ntype+1)

#     var = nco.createVariable(
#         var_name, 'f8', (type_dim_name, grid_dim_name),
#         fill_value=F8_FILLVAL
#     )
#     var.units = var_units
#     var.standard_name = var_name
#     var[:] = frac
#     nco.close()

# # def write_jules_frac(year, lc_names, frac_fn, surf_hgt_fn, one_d=False):
# #     frac, surf_hgt = get_jules_frac(year, lc_names)    
# #     ntype = frac.shape[0]
# #     if one_d:
# #         mask = LAND_FRAC > 0.
# #         mask = mask[None, :, :] * np.ones(ntype)[:, None, None]
# #         mask = mask.astype(bool)
# #         frac = frac.transpose()[mask.transpose()]
# #         surf_hgt = surf_hgt.transpose()[mask.transpose()]        
# #         write_jules_frac_1d(frac_fn, frac, 'frac', '1')
# #         write_jules_frac_1d(surf_hgt_fn, surf_hgt, 'elevation', 'm')
# #     else:
# #         write_jules_frac_2d(frac_fn, frac, 'frac', '1')
# #         write_jules_frac_2d(surf_hgt_fn, surf_hgt, 'elevation', 'm')

