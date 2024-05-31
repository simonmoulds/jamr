#!/usr/bin/env python3

import os
import re
import glob
import time
import math
import zipfile
import logging
import warnings

from typing import List 
from pathlib import Path
from collections import namedtuple
from subprocess import PIPE, DEVNULL

import grass.script as gscript
import grass.exceptions 

# import grass python libraries
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
from grass.pygrass.modules import Module 

from osgeo import gdal, gdalconst

from jamr.utils import *
from jamr.constants import REGIONS
from jamr.dataset import DS, SFDS, MFDS


class TerrestrialEcoregions(SFDS):
    def __init__(self, config, overwrite):
        super().__init__(config, overwrite)

    def initial(self):
        self.preprocess() 
        self.read() 

    def get_input_filenames(self):
        self.filenames = [self.config['landcover']['teow']['data_file']]
    
    def set_mapnames(self):
        self.mapnames = ['wwf_terr_ecos_globe_0.008333Deg']

    def preprocess(self):

        scratch = self.config['main']['scratch_directory']
        os.makedirs(scratch, exist_ok=True) # Just in case it's not been created yet
        
        # Extract data from zip archive
        with zipfile.ZipFile(self.filename, 'r') as f:
            f.extractall(scratch)

        shpfile = os.path.join(scratch, 'official', 'wwf_terr_ecos.shp')
        preprocessed_file = os.path.join(scratch, 'wwf_terr_ecos_0.008333Deg.tif')
        if not os.path.exists(preprocessed_file) or self.overwrite:
            rasterize_opts = gdal.RasterizeOptions(
                outputBounds=[-180, -90, 180, 90], 
                outputType=gdalconst.GDT_Byte,
                width=43200, height=21600, 
                allTouched=True, attribute='BIOME'
            )
            gdal.Rasterize(preprocessed_file, shpfile, options=rasterize_opts)

        self.preprocessed_filenames = [preprocessed_file] 

    def read(self):
        # try:
        #     r.in_gdal(input=self.preprocessed_filename, output=self.mapname, flags='a', overwrite=self.overwrite)
        # except grass.exceptions.CalledModuleError:
        #     pass
        p = gscript.start_command('r.in.gdal', input=self.preprocessed_filename, output=self.mapname, stderr=PIPE)
        stdout, stderr = p.communicate()



class C4Fraction(SFDS):
    def __init__(self, config, overwrite):
        super().__init__(config, overwrite)

    def initial(self):
        self.preprocess()
        self.read()

    def get_input_filenames(self):
        self.filenames = [self.config['landcover']['c4']['data_file']]

    def set_mapnames(self):
        self.mapnames = ['c4_distribution_nus_v2.2']

    def preprocess(self):
        scratch = self.config['main']['scratch_directory']
        os.makedirs(scratch, exist_ok=True) # Just in case it's not been created yet
        preprocessed_file = os.path.join(scratch, 'C4_distribution_NUS_v2.2.tif')
        if not os.path.exists(preprocessed_file) or self.overwrite:
            translate_opts = gdal.TranslateOptions(
                format='GTiff', outputSRS='EPSG:4326', 
                outputBounds=[-180, 90, 180, -90], 
                # width=43200, height=21600, resampleAlg='bilinear'
                width=720, height=360, resampleAlg='bilinear'
            )
            input_file = "NETCDF:" + self.filename + ":C4_area"
            gdal.Translate(preprocessed_file, input_file, options=translate_opts)

        self.preprocessed_filenames = [preprocessed_file]

    def read(self):
        # try:
        #     r.in_gdal(input=self.preprocessed_filename, output=self.mapname, flags='a', overwrite=self.overwrite)
        # except grass.exceptions.CalledModuleError:
        #     pass
        p = gscript.start_command('r.in.gdal', input=self.preprocessed_filename, output=self.mapname, stderr=PIPE)
        stdout, stderr = p.communicate()


class ESACCILC(MFDS):
    def __init__(self, config, overwrite):
        start_year = int(config['landcover']['esa']['start_year'])
        end_year = int(config['landcover']['esa']['end_year'])
        self.years = [yr for yr in range(start_year, end_year + 1)]
        self.categories = [
            10, 11, 12, 20, 30, 40, 50, 60, 61, 62, 70, 71, 72, 
            80, 81, 82, 90, 100, 110, 120, 121, 122, 130, 140, 
            150, 151, 152, 153, 160, 170, 180, 190, 200, 201, 202, 210, 220
        ]
        super().__init__(config, overwrite)

    def initial(self):
        self.preprocess()
        self.read()

    def _get_filename(self, year):
        if int(year) <= 2015:
            return f'ESACCI-LC-L4-LCCS-Map-300m-P1Y-{year}-v2.0.7.tif' 
        elif int(year) > 2015:
            return f'C3S-LC-L4-LCCS-Map-300m-P1Y-{year}-v2.1.1.tif'

    def get_input_filenames(self):
        datadir = self.config['landcover']['esa']['data_directory']
        files = {}
        for year in self.years:
            filename = self._get_filename(year)
            files[year] = os.path.join(datadir, filename)
        self.filenames = files 

    def set_mapnames(self):
        mapnames = {}
        for year in self.years:
            mapnames[year] = f'esacci_lc_{year}'
        self.mapnames = mapnames 

    def read(self):
        for year in self.years:
            filename = self.preprocessed_filenames[year]
            mapname = self.mapnames[year]
            # try:
            #     r.in_gdal(input=filename, output=mapname, flags='a', overwrite=self.overwrite)
            # except grass.exceptions.CalledModuleError:
            #     pass
            # This approach allows us to hide stdout/stderr:
            # https://grass.osgeo.org/grass83/manuals/libpython/pygrass_modules.html
            p = gscript.start_command('r.in.gdal', input=filename, output=mapname, stderr=PIPE)
            stdout, stderr = p.communicate()

    def __getitem__(self, index):
        return self.mapnames[index]

    def __len__(self):
        return len(self.mapnames) 


class ESACCIWB(SFDS):
    def __init__(self, config, overwrite):
        super().__init__(config, overwrite)

    def initial(self):
        self.preprocess()
        self.read()

    def get_input_filenames(self):
        self.filenames = [self.config['landfraction']['esa']['data_file']]

    def set_mapnames(self):
        self.mapnames = ['esa_water_bodies']

    def read(self):
        # try:
        #     r.in_gdal(input=self.preprocessed_filename, output=self.mapname, flags='a', overwrite=self.overwrite)
        # except grass.exceptions.CalledModuleError:
        #     pass 
        p = gscript.start_command('r.in.gdal', input=self.preprocessed_filename, output=self.mapname, stderr=PIPE)
        stdout, stderr = p.communicate()


POULTER_CROSSWALK = {
    'trees_broadleaf_evergreen': {
        30: 0.05, 40: 0.05, 50: 0.90, 100: 0.1, 110: 0.05, 150: 0.01, 160: 0.3, 170: 0.6
    },
    'trees_broadleaf_deciduous': {
        30: 0.05, 40: 0.05, 60: 0.70, 61: 0.70, 62: 0.30, 90: 0.30, 100: 0.20, 
        110: 0.10, 150: 0.03, 151: 0.02, 160: 0.30, 180: 0.05, 190: 0.025
    },
    'trees_needleleaf_evergreen': {
        70: 0.70, 71: 0.70, 72: 0.30, 90: 0.20, 100: 0.05, 110: 0.05, 150: 0.01, 151: 0.06, 180: 0.10, 190: 0.025
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
        151: 0.05, 152: 0.05, 153: 0.15, 160: 0.20, 180: 0.40, 190: 0.15
    },
    "crops": {
        10: 1.0, 11: 1.0, 12: 0.50, 20: 1.0, 30: 0.6, 40: 0.4
    }, 
    "bare_soil": {
        62: 0.10, 72: 0.30, 82: 0.30, 90: 0.10, 120: 0.20, 121: 0.20, 122: 0.20, 
        130: 0.40, 140: 0.40, 150: 0.85, 151: 0.85, 152: 0.85, 153: 0.85, 190: 0.75, 200: 1.0, 201: 1.0, 202: 1.0},
    "water": {160: 0.20, 170: 0.20, 180: 0.30, 190: 0.05, 210: 1.0}, 
    "snow_ice": {220: 1}
}


class Poulter2015PFT:
    def __init__(self, config, landcover, overwrite):
        self.config = config
        self.landcover = landcover 
        self.years = self.landcover.years
        self.pft_names = list(POULTER_CROSSWALK.keys())
        self.crosswalk = POULTER_CROSSWALK
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
        # large factor to convert the fractions in the crosswalk table to intgers 
        mult_factor = 1000
        self._write_reclass_rules(pft, factor=mult_factor)
        g.region(raster=input_map)
        # try:
        #     r.reclass(
        #         input=input_map, 
        #         output=output_map + '_step1', 
        #         rules='/tmp/rules.txt', 
        #         overwrite=self.overwrite
        #     )
        # except grass.exceptions.CalledModuleError:
        #     pass

        p = gscript.start_command('r.reclass', 
                                  input=input_map, 
                                  output=output_map + '_step1', 
                                  rules='/tmp/rules.txt', 
                                  overwrite=self.overwrite, stderr=PIPE)
        stdout, stderr = p.communicate()

        # # Step 2 - Divide by factor used to convert percentages to integers in step 1 
        # try:
        #     r.mapcalc(f'{output_map} = {output_map}_step1 / {mult_factor}', overwrite=self.overwrite)
        # except grass.exceptions.CalledModuleError:
        #     pass 
        p = gscript.start_command('r.mapcalc', 
                                  expression=f'{output_map} = {output_map}_step1 / {mult_factor}', 
                                  overwrite=self.overwrite, 
                                  stderr=PIPE)
        stdout, stderr = p.communicate()

        # # Resample to the current region
        # g.region(region=self.region)
        # try:
        #     r.resamp_stats(input=f'{output_map}_step2', output=output_map, method='average', overwrite=self.overwrite)
        # except grass.exceptions.CalledModuleError:
        #     pass 

    def compute(self):
        g.region(raster=self.landcover.mapnames[2015])
        for year in self.years:
            for pft in self.pft_names:
                self._create_pft_map(year, pft)

    def write(self):
        pass
        # output_directory = self.config['main']['output_directory']
        # for year in self.years:
        #     for pft in self.pfts:
        #         mapname = self.mapnames[year][pft]
        #         output_filename = os.path.join(output_directory, mapname + '.tif')
        #         r.out_gdal(input=mapname, output=output_filename, overwrite=self.overwrite)


class Poulter2015FivePFT:
    def __init__(self, config, inputdata, region, overwrite):
        self.config = config 
        self.inputdata = inputdata 
        self.years = inputdata.landcover.years 
        self.pft_names = ['tree_broadleaf', 'tree_needleleaf', 'shrub', 'c3_grass', 'c4_grass', 'urban', 'water', 'bare_soil', 'snow_ice']
        self.region = region
        self.overwrite = overwrite 
        self.set_mapnames()

    def set_mapnames(self):
        mapnames = {}
        for year in self.years:
            year_mapnames = {} 
            for pft in self.pft_names:
                year_mapnames[pft] = f'{pft}_{year}_{self.region}'
            
            mapnames[year] = year_mapnames

        self.mapnames = mapnames 

    def compute(self):
        self.compute_tree_broadleaf(2015)
        # self.compute_tree_needleleaf() 
        # self.compute_shrub()
        # self.compute_c3_grass()
        # self.compute_c4_grass() 
        # self.compute_urban()
        # self.compute_water()
        # self.compute_bare_soil()
        # self.compute_snow_ice()

    def compute_tree_broadleaf(self, year):
        output_map = self.mapnames[year]['tree_broadleaf']
        tree_broadleaf_deciduous_map = self.inputdata.pfts.mapnames[year]['trees_broadleaf_deciduous']
        tree_broadleaf_evergreen_map = self.inputdata.pfts.mapnames[year]['trees_broadleaf_evergreen']
        p = gscript.start_command('r.mapcalc', 
                                  expression=f'{output_map} = {tree_broadleaf_deciduous_map} + {tree_broadleaf_evergreen_map}',
                                  overwrite=self.overwrite, 
                                  stderr=PIPE)
        stdout, stderr = p.communicate()

    def compute_tree_needleleaf(self, year):
        output_map = self.mapnames[year]['tree_needleleaf']
        tree_needleleaf_deciduous_map = self.inputdata.pfts.mapnames[year]['tree_needleleaf_deciduous']
        tree_needleleaf_evergreen_map = self.inputdata.pfts.mapnames[year]['tree_needleleaf_evergreen']
        try:
            r.mapcalc(
                f'{output_map} = {tree_needleleaf_deciduous_map} + {tree_needleleaf_evergreen_map}', 
                overwrite=self.overwrite
            )
        except grass.exceptions.CalledModuleError:
            pass 

    def compute_shrub(self, year):
        output_map = self.mapnames[year]['shrub']
        shrub_broadleaf_deciduous_map = self.inputdata.pfts.mapnames[year]['shrub_broadleaf_deciduous'] 
        shrub_broadleaf_evergreen_map = self.inputdata.pfts.mapnames[year]['shrub_broadleaf_evergreen'] 
        shrub_needleleaf_deciduous_map = self.inputdata.pfts.mapnames[year]['shrub_needleleaf_deciduous'] 
        shrub_needleleaf_evergreen_map = self.inputdata.pfts.mapnames[year]['shrub_needleleaf_evergreen']
        try:
            r.mapcalc(
                f'{output_map} = {shrub_broadleaf_deciduous_map} + {shrub_broadleaf_evergreen_map} '
                f'+ {shrub_needleleaf_deciduous_map} + {shrub_needleleaf_evergreen_map}',
                overwrite=self.overwrite
            )
        except grass.exceptions.CalledModuleError:
            pass 

    def compute_c3_grass(self, year):
        output_map = self.mapnames[year]['c3_grass']
        natural_grass_map = self.inputdata.pfts.mapnames[year]['natural_grass']
        managed_grass_map = self.inputdata.pfts.mapnames[year]['managed_grass']
        c4_natural_vegetation_fraction_map = 'todo'
        c4_crop_fraction_map = 'todo'
        try:
            r.mapcalc(
                f'{output_map} = ({natural_grass_map} * (1 - {c4_natural_vegetation_fraction_map})) '
                f'+ ({managed_grass_map} * (1 - {c4_crop_fraction_map}))',
                overwrite=self.overwrite
            )
        except grass.exceptions.CalledModuleError:
            pass 

    def compute_c4_grass(self, year):
        output_map = self.mapnames[year]['c4_grass']
        natural_grass_map = self.inputdata.pfts.mapnames[year]['natural_grass']
        managed_grass_map = self.inputdata.pfts.mapnames[year]['managed_grass']
        c4_natural_vegetation_fraction_map = 'todo'
        c4_crop_fraction_map = 'todo'
        try:
            r.mapcalc(
                f'{output_map} = ({natural_grass_map} * {c4_natural_vegetation_fraction_map}) '
                f'+ ({managed_grass_map} * {c4_crop_fraction_map})',
                overwrite=self.overwrite
            )
        except grass.exceptions.CalledModuleError:
            pass 

    def compute_urban(self, year):
        output_map = self.mapnames[year]['urban']
        urban_map = self.inputdata.pfts.mapnames[year]['urban']
        try:
            r.mapcalc(f'{output_map} = {urban_map}', overwrite=self.overwrite)
        except grass.exceptions.CalledModuleError:
            pass 

    def compute_water(self, year):
        output_map = self.mapnames[year]['water']
        water_map = self.inputdata.pfts.mapnames[year]['water']
        try:
            r.mapcalc(f'{output_map} = {water_map}', overwrite=self.overwrite)
        except grass.exceptions.CalledModuleError:
            pass 

    def compute_bare_soil(self, year):
        output_map = self.mapnames[year]['bare_soil']
        bare_soil_map = self.inputdata.pfts.mapnames[year]['bare_soil']
        try:
            r.mapcalc(f'{output_map} = {bare_soil_map}', overwrite=self.overwrite)
        except grass.exceptions.CalledModuleError:
            pass 

    def compute_snow_ice(self, year):
        output_map = self.mapnames[year]['snow_ice']
        snow_ice_map = self.inputdata.pfts.mapnames[year]['snow_ice']
        try:
            r.mapcalc(f'{output_map} = {snow_ice_map}', overwrite=self.overwrite)
        except grass.exceptions.CalledModuleError:
            pass 


class Poulter2015NinePFT(Poulter2015FivePFT):
    pass


#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_tree_broadleaf_evergreen_x1000 \
# 	rules=$AUXDIR/tree_broadleaf_evergreen_reclass.txt \
# 	$OVERWRITE

#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_tree_broadleaf_evergreen_x1000 \
# 	rules=$AUXDIR/tree_broadleaf_evergreen_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_tree_broadleaf_evergreen_x1000 \
# 	output=esacci_lc_${YEAR}_tree_broadleaf_evergreen_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_tree_broadleaf_evergreen_globe_0.008333Deg = esacci_lc_${YEAR}_tree_broadleaf_evergreen_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE

# # ===========================================================
# # Import tropical forest area, infill
# # ===========================================================

# unzip -o ${DATADIR}/official_teow.zip -d ${AUXDIR}
# gdal_rasterize \
#     -at -te -180 -90 180 90 \
#     -ts 43200 21600 \
#     -a BIOME \
#     ../data/aux/official/wwf_terr_ecos.shp \
#     ../data/aux/wwf_terr_ecos_0.008333Deg.tif
# g.region region=globe_0.008333Deg
# r.in.gdal \
#     -a \
#     input=${AUXDIR}/wwf_terr_ecos_0.008333Deg.tif \
#     output=wwf_terr_ecos_globe_0.008333Deg \
#     ${OVERWRITE}
# r.null map=wwf_terr_ecos_globe_0.008333Deg setnull=0
# r.grow.distance \
#     input=wwf_terr_ecos_globe_0.008333Deg \
#     value=wwf_terr_ecos_globe_0.008333Deg_interp \
#     ${OVERWRITE}
# r.mapcalc \
#     "tropical_broadleaf_forest_globe_0.008333Deg = if((wwf_terr_ecos_globe_0.008333Deg_interp == 1) | (wwf_terr_ecos_globe_0.008333Deg_interp == 2), 1, 0)" \
#     ${OVERWRITE}

# # ===========================================================
# # Read C4 fraction data
# # ===========================================================

# # Run R script to make C4 fraction:
# NATFILE=${AUXDIR}/c4_nat_veg_frac_0.008333Deg.tif
# CROPFILE=${AUXDIR}/c4_crop_frac_0.008333Deg.tif
# if [[ ! -f ${NATFILE} || ! -f ${CROPFILE} || ${OVERWRITE} == '--overwrite' ]]   
# then    
#     Rscript $SRCDIR/rscript/make_c4_fraction.R
#     g.region region=globe_0.008333Deg
    
#     # r.external \
#     r.in.gdal \
# 	-a \
# 	input=${AUXDIR}/c4_nat_veg_frac_0.008333Deg.tif \
# 	output=c4_nat_veg_frac_globe_0.008333Deg \
# 	--overwrite
#     # r.external \
#     r.in.gdal \
# 	-a \
# 	input=${AUXDIR}/c4_crop_frac_0.008333Deg.tif \
# 	output=c4_crop_frac_globe_0.008333Deg \
# 	--overwrite
# fi

# # ===========================================================
# # Make JULES land cover fraction maps
# # ===========================================================

# chmod 755 $SRCDIR/bash/make_land_cover_fraction_lookup_tables.sh
# bash $SRCDIR/bash/make_land_cover_fraction_lookup_tables.sh

# declare -a YEARS=({1992..2015})
# # declare -a YEARS=(2015)

# # get elevation for land cells
# g.region region=globe_0.002778Deg

# # setting mask will ensure values outside land mask are set to null
# # esacci_land_frac_globe_0.002778Deg computed in grass_make_jules_land_frac.sh
# # r.external -a input=${AUXDIR}/dem/merit_dem_globe_0.002778Deg.tif output=merit_dem_globe_0.002778Deg --overwrite
# r.mask raster=esacci_land_frac_globe_0.002778Deg
# r.mapcalc \
#     "merit_dem_globe_0.002778Deg_surf_hgt = merit_dem_globe_0.002778Deg" \
#     --overwrite

# # land sea mask @ 0.002778Deg
# r.mapcalc \
#     "land_sea_mask = esacci_land_frac_globe_0.002778Deg" \
#     --overwrite
# r.mask -r

# # resample land elevation map to 1km maps, disregarding non-land cells
# g.region region=globe_0.008333Deg
# r.resamp.stats \
#     -w \
#     input=merit_dem_globe_0.002778Deg_surf_hgt \
#     output=merit_dem_globe_0.008333Deg_surf_hgt \
#     method=average \
#     --overwrite

# # Loop through years and create land cover fractions/surface heights
# for YEAR in "${YEARS[@]}"
# do
#     g.region region=globe_0.002778Deg
    
#     # r.external \
#     r.in.gdal \
# 	-a \
# 	input=${ESACCIDIR}/ESACCI-LC-L4-LCCS-Map-300m-P1Y-${YEAR}-v2.0.7.tif \
# 	output=esacci_lc_${YEAR}_w_sea \
# 	$OVERWRITE

#     # Mask sea values in esacci_lc_${YEAR}_w_sea by multiplying by
#     # land_sea_mask, in which non-land cells are null. 
#     r.mapcalc \
#     	"esacci_lc_${YEAR} = esacci_lc_${YEAR}_w_sea * land_sea_mask" \
#     	$OVERWRITE
	    
#     # tree broadleaf evergreen
#     # ########################
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_tree_broadleaf_evergreen_x1000 \
# 	rules=$AUXDIR/tree_broadleaf_evergreen_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_tree_broadleaf_evergreen_x1000 \
# 	output=esacci_lc_${YEAR}_tree_broadleaf_evergreen_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_tree_broadleaf_evergreen_globe_0.008333Deg = esacci_lc_${YEAR}_tree_broadleaf_evergreen_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_tree_broadleaf_evergreen = (0.05 * esacci_lc_${YEAR}_30) + (0.05 * esacci_lc_${YEAR}_40) + (0.90 * esacci_lc_${YEAR}_50) + (0.10 * esacci_lc_${YEAR}_100) + (0.05 * esacci_lc_${YEAR}_110) + (0.01 * esacci_lc_${YEAR}_150) + (0.30 * esacci_lc_${YEAR}_160) + (0.60 * esacci_lc_${YEAR}_170)" \
#     # 	$OVERWRITE
    
#     # tree broadleaf deciduous
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_tree_broadleaf_deciduous_x1000 \
# 	rules=$AUXDIR/tree_broadleaf_deciduous_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_tree_broadleaf_deciduous_x1000 \
# 	output=esacci_lc_${YEAR}_tree_broadleaf_deciduous_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_tree_broadleaf_deciduous_globe_0.008333Deg = esacci_lc_${YEAR}_tree_broadleaf_deciduous_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_tree_broadleaf_deciduous = (0.05 * esacci_lc_${YEAR}_30) + (0.05 * esacci_lc_${YEAR}_40) + (0.70 * esacci_lc_${YEAR}_60) + (0.70 * esacci_lc_${YEAR}_61) + (0.30 * esacci_lc_${YEAR}_62) + (0.30 * esacci_lc_${YEAR}_90) + (0.20 * esacci_lc_${YEAR}_100) + (0.10 * esacci_lc_${YEAR}_110) + (0.03 * esacci_lc_${YEAR}_150) + (0.02 * esacci_lc_${YEAR}_151) + (0.30 * esacci_lc_${YEAR}_160) + (0.05 * esacci_lc_${YEAR}_180) + (0.025 * esacci_lc_${YEAR}_190)" \
#     # 	$OVERWRITE

#     # tree needleleaf evergreen
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_tree_needleleaf_evergreen_x1000 \
# 	rules=$AUXDIR/tree_needleleaf_evergreen_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_tree_needleleaf_evergreen_x1000 \
# 	output=esacci_lc_${YEAR}_tree_needleleaf_evergreen_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_tree_needleleaf_evergreen_globe_0.008333Deg = esacci_lc_${YEAR}_tree_needleleaf_evergreen_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_tree_needleleaf_evergreen = (0.70 * esacci_lc_${YEAR}_70) + (0.70 * esacci_lc_${YEAR}_71) + (0.30 * esacci_lc_${YEAR}_72) + (0.20 * esacci_lc_${YEAR}_90) + (0.05 * esacci_lc_${YEAR}_100) + (0.05 * esacci_lc_${YEAR}_110) + (0.01 * esacci_lc_${YEAR}_150) + (0.06 * esacci_lc_${YEAR}_151) + (0.10 * esacci_lc_${YEAR}_180) + (0.025 * esacci_lc_${YEAR}_190)" \
#     # 	$OVERWRITE

#     # tree needleleaf deciduous
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_tree_needleleaf_deciduous_x1000 \
# 	rules=$AUXDIR/tree_needleleaf_deciduous_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_tree_needleleaf_deciduous_x1000 \
# 	output=esacci_lc_${YEAR}_tree_needleleaf_deciduous_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_tree_needleleaf_deciduous_globe_0.008333Deg = esacci_lc_${YEAR}_tree_needleleaf_deciduous_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_tree_needleleaf_deciduous = (0.70 * esacci_lc_${YEAR}_80) + (0.70 * esacci_lc_${YEAR}_81) + (0.30 * esacci_lc_${YEAR}_82) + (0.10 * esacci_lc_${YEAR}_90) + (0.05 * esacci_lc_${YEAR}_100) + (0.02 * esacci_lc_${YEAR}_151)" \
#     # 	$OVERWRITE

#     # shrub broadleaf evergreen
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_shrub_broadleaf_evergreen_x1000 \
# 	rules=$AUXDIR/shrub_broadleaf_evergreen_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_shrub_broadleaf_evergreen_x1000 \
# 	output=esacci_lc_${YEAR}_shrub_broadleaf_evergreen_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_shrub_broadleaf_evergreen_globe_0.008333Deg = esacci_lc_${YEAR}_shrub_broadleaf_evergreen_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_shrub_broadleaf_evergreen = (0.05 * esacci_lc_${YEAR}_30) + (0.075 * esacci_lc_${YEAR}_40) + (0.05 * esacci_lc_${YEAR}_50) + (0.05 * esacci_lc_${YEAR}_70) + (0.05 * esacci_lc_${YEAR}_71) + (0.05 * esacci_lc_${YEAR}_80) + (0.05 * esacci_lc_${YEAR}_81) + (0.05 * esacci_lc_${YEAR}_90) + (0.05 * esacci_lc_${YEAR}_100) + (0.05 * esacci_lc_${YEAR}_110) + (0.20 * esacci_lc_${YEAR}_120) + (0.30 * esacci_lc_${YEAR}_121) + (0.01 * esacci_lc_${YEAR}_150) + (0.02 * esacci_lc_${YEAR}_152) + (0.20 * esacci_lc_${YEAR}_170)" \
#     # 	$OVERWRITE

#     # shrub broadleaf deciduous
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_shrub_broadleaf_deciduous_x1000 \
# 	rules=$AUXDIR/shrub_broadleaf_deciduous_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_shrub_broadleaf_deciduous_x1000 \
# 	output=esacci_lc_${YEAR}_shrub_broadleaf_deciduous_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_shrub_broadleaf_deciduous_globe_0.008333Deg = esacci_lc_${YEAR}_shrub_broadleaf_deciduous_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_shrub_broadleaf_deciduous = (0.50 * esacci_lc_${YEAR}_12) + (0.05 * esacci_lc_${YEAR}_30) + (0.10 * esacci_lc_${YEAR}_40) + (0.05 * esacci_lc_${YEAR}_50) + (0.15 * esacci_lc_${YEAR}_60) + (0.15 * esacci_lc_${YEAR}_61) + (0.25 * esacci_lc_${YEAR}_62) + (0.05 * esacci_lc_${YEAR}_70) + (0.05 * esacci_lc_${YEAR}_71) + (0.05 * esacci_lc_${YEAR}_72) + (0.05 * esacci_lc_${YEAR}_80) + (0.05 * esacci_lc_${YEAR}_81) + (0.05 * esacci_lc_${YEAR}_82) + (0.05 * esacci_lc_${YEAR}_90) + (0.10 * esacci_lc_${YEAR}_100) + (0.10 * esacci_lc_${YEAR}_110) + (0.20 * esacci_lc_${YEAR}_120) + (0.60 * esacci_lc_${YEAR}_122) + (0.03 * esacci_lc_${YEAR}_150) + (0.06 * esacci_lc_${YEAR}_152) + (0.10 * esacci_lc_${YEAR}_180)" \
#     # 	$OVERWRITE

#     # shrub needleleaf evergreen
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_shrub_needleleaf_evergreen_x1000 \
# 	rules=$AUXDIR/shrub_needleleaf_evergreen_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_shrub_needleleaf_evergreen_x1000 \
# 	output=esacci_lc_${YEAR}_shrub_needleleaf_evergreen_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_shrub_needleleaf_evergreen_globe_0.008333Deg = esacci_lc_${YEAR}_shrub_needleleaf_evergreen_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_shrub_needleleaf_evergreen = (0.05 * esacci_lc_${YEAR}_30) + (0.075 * esacci_lc_${YEAR}_40) + (0.05 * esacci_lc_${YEAR}_70) + (0.05 * esacci_lc_${YEAR}_71) + (0.05 * esacci_lc_${YEAR}_72) + (0.05 * esacci_lc_${YEAR}_80) + (0.05 * esacci_lc_${YEAR}_81) + (0.05 * esacci_lc_${YEAR}_82) + (0.05 * esacci_lc_${YEAR}_90) + (0.05 * esacci_lc_${YEAR}_100) + (0.05 * esacci_lc_${YEAR}_110) + (0.20 * esacci_lc_${YEAR}_120) + (0.30 * esacci_lc_${YEAR}_121) + (0.01 * esacci_lc_${YEAR}_150) + (0.02 * esacci_lc_${YEAR}_152) + (0.05 * esacci_lc_${YEAR}_180)" \
#     # 	$OVERWRITE

#     # shrub neefleleaf deciduous
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_shrub_needleleaf_deciduous_x1000 \
# 	rules=$AUXDIR/shrub_needleleaf_deciduous_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_shrub_needleleaf_deciduous_x1000 \
# 	output=esacci_lc_${YEAR}_shrub_needleleaf_deciduous_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_shrub_needleleaf_deciduous_globe_0.008333Deg = esacci_lc_${YEAR}_shrub_needleleaf_deciduous_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_shrub_needleleaf_deciduous = 0" \
#     # 	$OVERWRITE

#     # natural grass
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_natural_grass_x1000 \
# 	rules=$AUXDIR/natural_grass_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_natural_grass_x1000 \
# 	output=esacci_lc_${YEAR}_natural_grass_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_natural_grass_globe_0.008333Deg = esacci_lc_${YEAR}_natural_grass_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_natural_grass = (0.15 * esacci_lc_${YEAR}_30) + (0.25 * esacci_lc_${YEAR}_40) + (0.15 * esacci_lc_${YEAR}_60) + (0.15 * esacci_lc_${YEAR}_61) + (0.35 * esacci_lc_${YEAR}_62) + (0.15 * esacci_lc_${YEAR}_70) + (0.15 * esacci_lc_${YEAR}_71) + (0.30 * esacci_lc_${YEAR}_72) + (0.15 * esacci_lc_${YEAR}_80) + (0.15 * esacci_lc_${YEAR}_81) + (0.30 * esacci_lc_${YEAR}_82) + (0.15 * esacci_lc_${YEAR}_90) + (0.40 * esacci_lc_${YEAR}_100) + (0.60 * esacci_lc_${YEAR}_110) + (0.20 * esacci_lc_${YEAR}_120) + (0.20 * esacci_lc_${YEAR}_121) + (0.20 * esacci_lc_${YEAR}_122) + (0.60 * esacci_lc_${YEAR}_130) + (0.60 * esacci_lc_${YEAR}_140) + (0.05 * esacci_lc_${YEAR}_150) + (0.05 * esacci_lc_${YEAR}_151) + (0.05 * esacci_lc_${YEAR}_152) + (0.15 * esacci_lc_${YEAR}_153) + (0.20 * esacci_lc_${YEAR}_160) + (0.40 * esacci_lc_${YEAR}_180) + (0.15 * esacci_lc_${YEAR}_190)" \
#     # 	$OVERWRITE

#     # managed grass
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_managed_grass_x1000 \
# 	rules=$AUXDIR/managed_grass_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_managed_grass_x1000 \
# 	output=esacci_lc_${YEAR}_managed_grass_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_managed_grass_globe_0.008333Deg = esacci_lc_${YEAR}_managed_grass_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_managed_grass = (1 * esacci_lc_${YEAR}_10) + (1 * esacci_lc_${YEAR}_11) + (0.50 * esacci_lc_${YEAR}_12) + (1 * esacci_lc_${YEAR}_20) + (0.60 * esacci_lc_${YEAR}_30) + (0.40 * esacci_lc_${YEAR}_40)" \
#     # 	$OVERWRITE

#     # urban
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_urban_x1000 \
# 	rules=$AUXDIR/urban_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_urban_x1000 \
# 	output=esacci_lc_${YEAR}_urban_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_urban_globe_0.008333Deg = esacci_lc_${YEAR}_urban_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_urban = (0.75 * esacci_lc_${YEAR}_190)" \
#     # 	$OVERWRITE

#     # bare soil
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_bare_soil_x1000 \
# 	rules=$AUXDIR/bare_soil_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_bare_soil_x1000 \
# 	output=esacci_lc_${YEAR}_bare_soil_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_bare_soil_globe_0.008333Deg = esacci_lc_${YEAR}_bare_soil_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_bare_soil = (0.10 * esacci_lc_${YEAR}_62) + (0.30 * esacci_lc_${YEAR}_72) + (0.30 * esacci_lc_${YEAR}_82) + (0.10 * esacci_lc_${YEAR}_90) + (0.20 * esacci_lc_${YEAR}_120) + (0.20 * esacci_lc_${YEAR}_121) + (0.20 * esacci_lc_${YEAR}_122) + (0.40 * esacci_lc_${YEAR}_130) + (0.40 * esacci_lc_${YEAR}_140) + (0.85 * esacci_lc_${YEAR}_150) + (0.85 * esacci_lc_${YEAR}_151) + (0.85 * esacci_lc_${YEAR}_152) + (0.85 * esacci_lc_${YEAR}_153) + (1 * esacci_lc_${YEAR}_200) + (1 * esacci_lc_${YEAR}_201) + (1 * esacci_lc_${YEAR}_202)" \
#     # 	$OVERWRITE

#     # water
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_water_x1000 \
# 	rules=$AUXDIR/water_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_water_x1000 \
# 	output=esacci_lc_${YEAR}_water_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_water_globe_0.008333Deg = esacci_lc_${YEAR}_water_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_water = (0.20 * esacci_lc_${YEAR}_160) + (0.20 * esacci_lc_${YEAR}_170) + (0.30 * esacci_lc_${YEAR}_180) + (0.05 * esacci_lc_${YEAR}_190) + (1 * esacci_lc_${YEAR}_210)" \
#     # 	$OVERWRITE

#     # snow/ice
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_snow_ice_x1000 \
# 	rules=$AUXDIR/snow_ice_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_snow_ice_x1000 \
# 	output=esacci_lc_${YEAR}_snow_ice_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_snow_ice_globe_0.008333Deg = esacci_lc_${YEAR}_snow_ice_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_snow_ice = (1 * esacci_lc_${YEAR}_220)" \
#     # 	$OVERWRITE

#     # no data
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_nodata_x1000 \
# 	rules=$AUXDIR/nodata_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_nodata_x1000 \
# 	output=esacci_lc_${YEAR}_nodata_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_nodata_globe_0.008333Deg = esacci_lc_${YEAR}_nodata_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_nodata = (1 * esacci_lc_${YEAR}_0)" \
#     # 	$OVERWRITE
    
#     # ===================================================== #
#     # Convert to JULES land cover types
#     # ===================================================== #
#     g.region region=globe_0.008333Deg

#     # (i) 5 PFT    
#     r.mapcalc \
# 	"lc_tree_broadleaf_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_tree_broadleaf_evergreen_globe_0.008333Deg + esacci_lc_${YEAR}_tree_broadleaf_deciduous_globe_0.008333Deg" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_tree_needleleaf_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_tree_needleleaf_evergreen_globe_0.008333Deg + esacci_lc_${YEAR}_tree_needleleaf_deciduous_globe_0.008333Deg" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_shrub_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_shrub_broadleaf_evergreen_globe_0.008333Deg + esacci_lc_${YEAR}_shrub_broadleaf_deciduous_globe_0.008333Deg + esacci_lc_${YEAR}_shrub_needleleaf_evergreen_globe_0.008333Deg + esacci_lc_${YEAR}_shrub_needleleaf_deciduous_globe_0.008333Deg" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_c4_grass_${YEAR}_globe_0.008333Deg = (esacci_lc_${YEAR}_natural_grass_globe_0.008333Deg * c4_nat_veg_frac_globe_0.008333Deg) + (esacci_lc_${YEAR}_managed_grass_globe_0.008333Deg * c4_crop_frac_globe_0.008333Deg)" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_c3_grass_${YEAR}_globe_0.008333Deg = (esacci_lc_${YEAR}_natural_grass_globe_0.008333Deg * (1-c4_nat_veg_frac_globe_0.008333Deg)) + (esacci_lc_${YEAR}_managed_grass_globe_0.008333Deg * (1-c4_crop_frac_globe_0.008333Deg))" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_urban_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_urban_globe_0.008333Deg" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_water_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_water_globe_0.008333Deg" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_bare_soil_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_bare_soil_globe_0.008333Deg" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_snow_ice_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_snow_ice_globe_0.008333Deg" \
# 	$OVERWRITE

#     # weighted elevation
#     for LC in tree_broadleaf tree_needleleaf shrub c4_grass c3_grass urban water bare_soil snow_ice
#     do
# 	r.mapcalc \
# 	    "lc_${LC}_${YEAR}_globe_0.008333Deg_weighted_elev = lc_${LC}_${YEAR}_globe_0.008333Deg * merit_dem_globe_0.008333Deg_surf_hgt" \
# 	    $OVERWRITE
#     done

#     # (ii) 9 PFT
#     r.mapcalc \
# 	"lc_tree_broadleaf_evergreen_tropical_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_tree_broadleaf_evergreen_globe_0.008333Deg * tropical_broadleaf_forest_globe_0.008333Deg" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_tree_broadleaf_evergreen_temperate_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_tree_broadleaf_evergreen_globe_0.008333Deg * (1-tropical_broadleaf_forest_globe_0.008333Deg)" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_tree_broadleaf_deciduous_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_tree_broadleaf_deciduous_globe_0.008333Deg" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_tree_needleleaf_evergreen_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_tree_needleleaf_evergreen_globe_0.008333Deg" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_tree_needleleaf_deciduous_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_tree_needleleaf_deciduous_globe_0.008333Deg" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_shrub_evergreen_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_shrub_broadleaf_evergreen_globe_0.008333Deg + esacci_lc_${YEAR}_shrub_needleleaf_evergreen_globe_0.008333Deg" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_shrub_deciduous_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_shrub_broadleaf_deciduous_globe_0.008333Deg + esacci_lc_${YEAR}_shrub_needleleaf_deciduous_globe_0.008333Deg" \
# 	$OVERWRITE

#     # weighted elevation
#     for LC in tree_broadleaf_evergreen_tropical tree_broadleaf_evergreen_temperate tree_broadleaf_deciduous tree_needleleaf_evergreen tree_needleleaf_deciduous shrub_evergreen shrub_deciduous
#     do
# 	r.mapcalc \
# 	    "lc_${LC}_${YEAR}_globe_0.008333Deg_weighted_elev = lc_${LC}_${YEAR}_globe_0.008333Deg * merit_dem_globe_0.008333Deg_surf_hgt" \
# 	    $OVERWRITE
#     done
    
# done
