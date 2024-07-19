#!/usr/bin/env python3

import os
import logging

from subprocess import PIPE

import grass.script as gscript

from jamr.process.ancillarydataset import AncillaryDataset
from jamr.utils.utils import *


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


class Poulter2015PFT:
    def __init__(self, config, landcover, overwrite):
        self.config = config
        self.landcover = landcover 
        self.years = self.landcover.years
        self.pft_names = list(ADJUSTED_POULTER_CROSSWALK.keys())
        self.crosswalk = ADJUSTED_POULTER_CROSSWALK
        self.overwrite = overwrite 
        self.set_mapnames()

    def initial(self):
        pass

    def _write_reclass_rules(self, pft, factor=1000):
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
        with open("/tmp/rules.txt", "w") as f:
            f.write(text)

    def set_mapnames(self):
        mapnames = {}
        for year in self.years:
            year_mapnames = {} 
            for pft in self.pft_names:
                year_mapnames[pft] = f'esacci_lc_{year}_{pft}'
            
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
        
        g.region(raster=input_map)
        p = gscript.start_command('r.reclass', 
                                  input=input_map, 
                                  output=output_map + '_step1', 
                                  rules='/tmp/rules.txt', 
                                  overwrite=self.overwrite, stderr=PIPE)
        stdout, stderr = p.communicate()

        # Divide by factor used to convert percentages to integers in step 1 
        p = gscript.start_command('r.mapcalc', 
                                  expression=f'{output_map} = {output_map}_step1 / {mult_factor}', 
                                  overwrite=self.overwrite, 
                                  stderr=PIPE)
        stdout, stderr = p.communicate()

    def compute(self):
        g.region(raster=self.landcover.mapnames[2015])
        for year in self.years:
            for pft in self.pft_names:
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
        self._compute_pfts()
        self._set_mapnames()

    def _compute_pfts(self):
        self.pfts = Poulter2015PFT(self.config, self.inputdata.landcover, self.overwrite)
        self.pfts.initial()
        self.pfts.compute()

    def _set_mapnames(self):
        mapnames_native = {}
        mapnames = {}
        for year in self.years:
            year_mapnames_native = {}
            year_mapnames = {} 
            for pft in self.pft_names:
                year_mapnames_native[pft] = f'{pft}_{year}_{self.region_name}_native'
                year_mapnames[pft] = f'{pft}_{year}_{self.region_name}.tif'
            
            mapnames_native[year] = year_mapnames_native 
            mapnames[year] = year_mapnames

        self.mapnames_native = mapnames_native
        self.mapnames = mapnames 

    def compute(self):
        raise NotImplementedError 

    def compute_c3_grass(self, year):
        LOGGER.debug(f'Computing C3 grass')
        native_output_map = self.mapnames_native[year]['c3_grass']
        output_map = self.mapnames[year]['c3_grass']
        natural_grass_map = self.pfts.mapnames[year]['natural_grass']
        managed_grass_map = self.pfts.mapnames[year]['crops']
        c4_natural_vegetation_fraction_map = self.inputdata.c4fraction.mapnames[2015]['C4_grass_area']
        c4_crop_fraction_map = self.inputdata.c4fraction.mapnames[2015]['C4_crop_area']
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc',
                                  expression=f'{native_output_map} = ({natural_grass_map} * (1 - {c4_natural_vegetation_fraction_map})) + ({managed_grass_map} * (1 - {c4_crop_fraction_map}))',
                                  overwrite=self.overwrite,
                                  stderr=PIPE)
        p.communicate()
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')

    def compute_c4_grass(self, year):
        LOGGER.debug(f'Computing C4 grass')
        native_output_map = self.mapnames_native[year]['c4_grass']
        output_map = self.mapnames[year]['c4_grass']
        natural_grass_map = self.pfts.mapnames[year]['natural_grass']
        managed_grass_map = self.pfts.mapnames[year]['crops']
        c4_natural_vegetation_fraction_map = self.inputdata.c4fraction.mapnames[2015]['C4_grass_area']
        c4_crop_fraction_map = self.inputdata.c4fraction.mapnames[2015]['C4_crop_area']
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc',
                                  expression=f'{native_output_map} = ({natural_grass_map} * {c4_natural_vegetation_fraction_map}) + ({managed_grass_map} * {c4_crop_fraction_map})',
                                  overwrite=self.overwrite,
                                  stderr=PIPE)
        p.communicate()
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')

    def compute_urban(self, year):
        LOGGER.debug(f'Computing urban land')
        native_output_map = self.mapnames_native[year]['urban']
        output_map = self.mapnames[year]['urban']
        urban_map = self.pfts.mapnames[year]['urban']
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc',
                                  expression=f'{native_output_map} = {urban_map}',
                                  overwrite=self.overwrite,
                                  stderr=PIPE)
        p.communicate()
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')

    def compute_water(self, year):
        LOGGER.debug(f'Computing water')
        native_output_map = self.mapnames_native[year]['water']
        output_map = self.mapnames[year]['water']
        water_map = self.pfts.mapnames[year]['water']
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc',
                                  expression=f'{native_output_map} = {water_map}',
                                  overwrite=self.overwrite,
                                  stderr=PIPE)
        p.communicate()
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')

    def compute_bare_soil(self, year):
        LOGGER.debug(f'Computing bare soil')
        native_output_map = self.mapnames_native[year]['bare_soil']
        output_map = self.mapnames[year]['bare_soil']
        bare_soil_map = self.pfts.mapnames[year]['bare_soil']
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc',
                                  expression=f'{native_output_map} = {bare_soil_map}', 
                                  overwrite=self.overwrite,
                                  stderr=PIPE)
        p.communicate()
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')

    def compute_snow_ice(self, year):
        LOGGER.debug(f'Computing snow/ice')
        native_output_map = self.mapnames_native[year]['snow_ice']
        output_map = self.mapnames[year]['snow_ice']
        snow_ice_map = self.pfts.mapnames[year]['snow_ice']
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc',
                                  expression=f'{native_output_map} = {snow_ice_map}', 
                                  overwrite=self.overwrite,
                                  stderr=PIPE)
        p.communicate()
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')

    def write(self):
        for year in self.years:
            for pft in self.pft_names:
                mapname = self.mapnames[year][pft]
                print(mapname)


class Poulter2015FivePFT(Poulter2015JulesPFT):
    def __init__(self, config, inputdata, overwrite):
        super().__init__(config, inputdata, 5, overwrite)

    def compute(self):
        self.compute_tree_broadleaf(2015)
        self.compute_tree_needleleaf(2015) 
        self.compute_shrub(2015)
        self.compute_c3_grass(2015)
        self.compute_c4_grass(2015)
        self.compute_urban(2015)
        self.compute_water(2015)
        self.compute_bare_soil(2015)
        self.compute_snow_ice(2015)

    def compute_tree_broadleaf(self, year):
        LOGGER.info(f'Computing broadleaf tree')
        native_output_map = self.mapnames_native[year]['tree_broadleaf']
        output_map = self.mapnames[year]['tree_broadleaf']
        tree_broadleaf_deciduous_map = self.pfts.mapnames[year]['trees_broadleaf_deciduous']
        tree_broadleaf_evergreen_map = self.pfts.mapnames[year]['trees_broadleaf_evergreen']
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc', 
                                  expression=f'{native_output_map} = {tree_broadleaf_deciduous_map} + {tree_broadleaf_evergreen_map}',
                                  overwrite=self.overwrite, 
                                  stderr=PIPE)
        p.communicate()
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')

    def compute_tree_needleleaf(self, year):
        LOGGER.info(f'Computing needleleaf tree')
        native_output_map = self.mapnames_native[year]['tree_needleleaf']
        output_map = self.mapnames[year]['tree_needleleaf']
        tree_needleleaf_deciduous_map = self.pfts.mapnames[year]['trees_needleleaf_deciduous']
        tree_needleleaf_evergreen_map = self.pfts.mapnames[year]['trees_needleleaf_evergreen']
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc', 
                                  expression=f'{native_output_map} = {tree_needleleaf_deciduous_map} + {tree_needleleaf_evergreen_map}', 
                                  overwrite=self.overwrite, 
                                  stderr=PIPE)
        p.communicate()
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
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')


class Poulter2015NinePFT(Poulter2015JulesPFT):
    def __init__(self, config, inputdata, overwrite):
        super().__init__(config, inputdata, 9, overwrite)
    
    def compute(self):
        grass_set_region_from_raster(raster=self.inputdata.landcover.mapnames[2015],
                                     n=self.config['region']['north'],
                                     s=self.config['region']['south'],
                                     e=self.config['region']['east'],
                                     w=self.config['region']['west'])
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
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')
    
    def compute_shrub_evergreen(self, year):
        native_output_map = self.mapnames_native[year]['shrub_evergreen']
        output_map = self.mapnames[year]['shrub_evergreen']
        shrub_broadleaf_evergreen_map = self.pfts.mapnames[year]['shrubs_broadleaf_evergreen'] 
        shrub_needleleaf_evergreen_map = self.pfts.mapnames[year]['shrubs_needleleaf_evergreen']
        self._set_native_region(self.inputdata.landcover.mapnames[2015])
        p = gscript.start_command('r.mapcalc', 
                                  expression=f'{output_map} = {shrub_broadleaf_evergreen_map} + {shrub_needleleaf_evergreen_map}',
                                  overwrite=self.overwrite, 
                                  stderr=PIPE)
        p.communicate()
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
        self._set_target_region()
        self._resample(input_map=native_output_map, output_map=output_map, method='average')